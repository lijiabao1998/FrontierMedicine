"""Independent CSV arithmetic. No author import, fitting, or new samples."""
import argparse,copy,csv,hashlib,json,math,sys,traceback
from pathlib import Path
from admission_guard import require_admission
from common import compare
HERE=Path(__file__).resolve().parent
SEEDS=[101,202,303,404,505]
SITES=['A_reference','B_intercept','C_measurement']
GROUPS=['x1_negative','x1_nonnegative']
HEADER=['row_id','seed','site','split','x1','x2','observed_x1','observed_x2','missing_x2','y','p_true','fixed_logit','p_fixed','p_recalibrated']
Z=1.959963984540054; T4=2.7764451051977987;TOL=1e-10
EXPECTED_CONTROLS=('N_PLUS_ONE','POSITIVES_PLUS_ONE','FIXED_BRIER_PLUS_1E4','RECALIBRATED_BRIER_PLUS_1E4','DELTA_MEAN_PLUS_1E4','DELTA_SE_PLUS_1E4','DELTA_CI_LOWER_MINUS_1E4','DELTA_CI_UPPER_PLUS_1E4','AGGREGATE_MEAN_PLUS_1E4','AGGREGATE_SE_PLUS_1E4','DELETE_SUBGROUP','NAN_DELTA_MEAN')

def summary(values,critical):
    n=len(values)
    if n<2:raise ValueError('insufficient observations')
    mean=math.fsum(values)/n
    se=math.sqrt(math.fsum((v-mean)**2 for v in values)/(n-1)/n)
    return {'n':n,'mean':mean,'standard_error':se,'interval95':[mean-critical*se,mean+critical*se]}

def project(author):
    runs={};aggs={}
    for row in author['runs']:
        key=str(row['seed'])+'_'+row['site']
        if key in runs:raise ValueError('duplicate run')
        if set(row['subgroups'])!=set(GROUPS):raise ValueError('group domain')
        runs[key]={g:{k:row['subgroups'][g][k] for k in ['n','positives','fixed_brier','recalibrated_brier','paired_brier_delta_conditional']} for g in GROUPS}
    for row in author['aggregates']:
        if row['site'] in aggs:raise ValueError('duplicate aggregate')
        aggs[row['site']]=row['subgroup_delta_brier']
    return {'runs':runs,'aggregates':aggs}

def calculate():
    manifest=json.loads((HERE/'SOURCE_MANIFEST.json').read_text())
    for row in manifest['files']:
        if hashlib.sha256((HERE/row['snapshot']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('frozen blob hash '+row['path'])
    author=json.loads((HERE/'reference/author-results.json').read_text())
    legacy=json.loads((HERE/'reference/author-manifest.json').read_text())
    if legacy['results.json']!=hashlib.sha256((HERE/'reference/author-results.json').read_bytes()).hexdigest():raise ValueError('legacy result hash')
    result={'runs':{},'aggregates':{}}; ids=set();raw_rows=0;checks=[]
    aruns={(r['seed'],r['site']):r for r in author['runs']}
    if len(aruns)!=15 or len(author['runs'])!=15:raise ValueError('author run domain')
    for seed in SEEDS:
        for site in SITES:
            filename=f'{seed}_{site}.csv';path=HERE/'reference/raw'/filename
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if legacy['raw/'+filename]!=digest:raise ValueError('legacy raw hash')
            groups={g:[] for g in GROUPS};cal=0;ev=[]
            with path.open(encoding='utf-8',newline='') as f:
                reader=csv.DictReader(f)
                if reader.fieldnames!=HEADER:raise ValueError('CSV header')
                for row in reader:
                    if set(row)!=set(HEADER) or None in row or any(v is None for v in row.values()):raise ValueError('malformed row')
                    if row['row_id'] in ids:raise ValueError('duplicate row id')
                    ids.add(row['row_id']);raw_rows+=1
                    if int(row['seed'])!=seed or row['site']!=site:raise ValueError('seed/site mismatch')
                    vals={k:float(row[k]) for k in HEADER if k not in ['row_id','seed','site','split']}
                    if not all(math.isfinite(v) for v in vals.values()):raise ValueError('nonfinite CSV')
                    if vals['y'] not in [0,1] or vals['missing_x2'] not in [0,1]:raise ValueError('binary domain')
                    if any(not 0<=vals[k]<=1 for k in ['p_true','p_fixed','p_recalibrated']):raise ValueError('probability domain')
                    if row['split']=='calibration':cal+=1
                    elif row['split']=='evaluation':
                        ev.append(vals);groups[GROUPS[0] if vals['x1']<0 else GROUPS[1]].append(vals)
                    else:raise ValueError('split domain')
            if cal!=256 or len(ev)!=512:raise ValueError('split counts')
            mapped={}
            for group,rows in groups.items():
                bf=[(r['y']-r['p_fixed'])**2 for r in rows];br=[(r['y']-r['p_recalibrated'])**2 for r in rows]
                mapped[group]={'n':len(rows),'positives':sum(int(r['y']) for r in rows),'fixed_brier':math.fsum(bf)/len(rows),
                  'recalibrated_brier':math.fsum(br)/len(rows),'paired_brier_delta_conditional':summary([b-a for a,b in zip(bf,br)],Z)}
            r=aruns[seed,site]
            if sum(x['n'] for x in mapped.values())!=512 or sum(x['positives'] for x in mapped.values())!=r['fixed']['positives']:raise ValueError('group sum counts')
            for field,model in [('fixed_brier','fixed'),('recalibrated_brier','recalibrated')]:
                if abs(math.fsum(x['n']*x[field] for x in mapped.values())/512-r[model]['brier'])>TOL:raise ValueError('group Brier sum')
            weighted=math.fsum(x['n']*x['paired_brier_delta_conditional']['mean'] for x in mapped.values())/512
            if abs(weighted-r['paired_brier_delta']['mean'])>TOL:raise ValueError('group delta sum')
            key=f'{seed}_{site}';result['runs'][key]=mapped
            checks.append({'filename':filename,'sha256':digest,'n_calibration':cal,'n_evaluation':len(ev),'group_sum_consistent':True})
    if raw_rows!=11520 or len(ids)!=11520:raise ValueError('total row count')
    for site in SITES:
        result['aggregates'][site]={g:summary([result['runs'][f'{s}_{site}'][g]['paired_brier_delta_conditional']['mean'] for s in SEEDS],T4) for g in GROUPS}
    return result,project(author),checks

def mutate(doc,control):
    path=control['path'];parent=doc
    for key in path[:-1]:parent=parent[key]
    if control['operation']=='delete':del parent[path[-1]]
    elif control['operation']=='nan':parent[path[-1]]=float('nan')
    else:parent[path[-1]]+=control['delta']

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--round',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    require_admission(a.repo,a.round,'MED-001',HERE/'PROTOCOL.json')
    protocol=json.loads((HERE/'PROTOCOL.json').read_text())
    if tuple(c['name'] for c in protocol['controls'])!=EXPECTED_CONTROLS:raise ValueError('frozen control domain/order')
    anchors=protocol['aggregate_delta_anchors']
    if len(anchors)!=6 or [(s,g) for s,g,v in anchors]!=[(s,g) for s in SITES for g in GROUPS]:raise ValueError('anchor domain')
    expected,author,checks=calculate();clean=compare(expected,author,TOL)
    controls=[];out=Path(a.output).parent;mdir=out/'mutants';mdir.mkdir()
    for c in protocol['controls']:
        mutant=copy.deepcopy(author);mutate(mutant,c);ver=compare(expected,mutant,TOL)
        (mdir/(c['name']+'.json')).write_text(json.dumps(mutant,indent=2)+'\n',encoding='utf-8')
        controls.append({'name':c['name'],'semantic_rejected':not ver['accepted'],'validation':ver})
    anchor_checks=[abs(expected['aggregates'][s][g]['mean']-v)<=TOL for s,g,v in anchors]
    ok=clean['accepted'] is True and len(controls)==12 and all(c['semantic_rejected'] is True for c in controls) and len(anchor_checks)==6 and all(x is True for x in anchor_checks)
    payload={'verdict':'INDEPENDENT_SYNTHETIC_SUBGROUP_ARITHMETIC_PASS' if ok else 'FAIL_CLOSED_SUBGROUP_ARITHMETIC','all_criteria_passed':ok,'source_integrity':True,
      'rows':11520,'raw_files':15,'run_groups':30,'site_group_aggregates':6,'clean_validation':clean,'controls':controls,'anchor_checks':anchor_checks,
      'raw_checks':checks,'independent':expected,'limits':protocol['limits'],'broad_problem_completion':False,'author_code_imported':False,'samples_generated':0,'fits':0}
    Path(a.output).write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in payload.items() if k not in ['independent','raw_checks','controls']},allow_nan=False));return 0 if ok else 1

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(json.dumps({'verdict':'INCOMPLETE_FAIL_CLOSED','error':str(e)}),file=sys.stderr);traceback.print_exc();sys.exit(2)
