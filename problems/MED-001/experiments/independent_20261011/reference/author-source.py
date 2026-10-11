#!/usr/bin/env python3
"""COMPLETELY SYNTHETIC methods demonstration. No patient/clinical predictions."""
import argparse, csv, hashlib, io, json, platform, sys, time
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import rankdata, t

SPEC_HASH = 'cb8e12aad804940aac4f4db855b1a62302f6abc372a9210f9baaf25939e5dfdd'
ROUND = '20261009T105245957548Z-gpt-MED-001'
COLUMNS = ['row_id','seed','site','split','x1','x2','observed_x1','observed_x2','missing_x2','y','p_true','fixed_logit','p_fixed','p_recalibrated']

def digest(data):
    return hashlib.sha256(data).hexdigest()

def json_bytes(obj):
    return (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()

def sigmoid(z):
    return 1/(1+np.exp(-np.clip(z,-35,35)))

def auc(y,p):
    n1=int(np.sum(y)); n0=len(y)-n1
    if n1==0 or n0==0: raise ValueError('AUROC undefined: single class')
    ranks=rankdata(p,method='average')
    return float((np.sum(ranks[y==1])-n1*(n1+1)/2)/(n1*n0))

def ap(y,p):
    if not np.sum(y): raise ValueError('AP undefined: no positives')
    order=np.argsort(-p,kind='stable'); ys=y[order]; ps=p[order]
    ends=np.r_[np.flatnonzero(np.diff(ps))+1,len(ps)]
    tp=np.cumsum(ys)[ends-1]
    return float(np.sum(np.diff(np.r_[0,tp])*tp/ends)/np.sum(y))

def brier(y,p): return float(np.mean((y-p)**2))

def net_benefit(y,p,threshold):
    selected=p>=threshold
    return float(np.mean(selected*y)-np.mean(selected*(1-y))*threshold/(1-threshold))

def fit_logistic(logit,y):
    X=np.column_stack([np.ones(len(y)),logit]); beta=np.array([0.,1.])
    if not np.all(np.isin(y,[0,1])) or len(np.unique(y))!=2: raise ValueError('binary two-class labels required')
    for iteration in range(1,101):
        p=sigmoid(X@beta); w=p*(1-p)
        h=X.T@(w[:,None]*X); g=X.T@(y-p)
        delta=np.linalg.solve(h,g); beta+=delta
        if np.max(np.abs(delta))<1e-10:
            return beta,iteration
    raise ValueError('logistic fit iteration cap reached')

def encode(rows):
    buffer=io.StringIO(newline=''); writer=csv.DictWriter(buffer,fieldnames=COLUMNS,lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return buffer.getvalue().encode()

def guard_rows(rows,expected_hash=None):
    if len({r['row_id'] for r in rows})!=len(rows): raise ValueError('duplicate row ID / split leakage')
    if expected_hash is not None and digest(encode(rows))!=expected_hash: raise ValueError('sealed data hash mismatch / label tampering')
    for row in rows:
        if row['split'] not in ['calibration','evaluation']: raise ValueError('unknown split')
        if row['y'] not in [0,1]: raise ValueError('non-binary label')

def guard_model(candidate,frozen):
    if digest(json_bytes(candidate))!=digest(json_bytes(frozen)): raise ValueError('fixed model tampering')

def calibrate(cal_rows,eval_rows,model,frozen):
    guard_model(model,frozen); guard_rows(cal_rows+eval_rows)
    if any(r['split']!='calibration' for r in cal_rows): raise ValueError('evaluation rows in calibrator fit')
    if any(r['split']!='evaluation' for r in eval_rows): raise ValueError('wrong evaluation split')
    beta,it=fit_logistic(np.array([r['fixed_logit'] for r in cal_rows]),np.array([r['y'] for r in cal_rows]))
    for row in cal_rows+eval_rows: row['p_recalibrated']=float(sigmoid(beta[0]+beta[1]*row['fixed_logit']))
    return beta,it

def summary(values,critical=1.959963984540054):
    values=np.asarray(values); n=len(values); mean=float(np.mean(values))
    se=float(np.std(values,ddof=1)/np.sqrt(n)) if n>1 else None
    return {'n':n,'mean':mean,'standard_error':se,'interval95':[mean-critical*se,mean+critical*se] if se is not None else None}

def metrics(rows,key):
    y=np.array([r['y'] for r in rows]); p=np.array([r[key] for r in rows]); n=len(y)
    if not np.all(np.isfinite(p)) or np.min(p)<=0 or np.max(p)>=1: raise ValueError('invalid probabilities')
    beta,it=fit_logistic(np.log(p/(1-p)),y)
    bins=[]
    for i in range(10):
        mask=(p>=i/10)&(p<(i+1)/10)
        bins.append({'lower':i/10,'upper':(i+1)/10,'n':int(mask.sum()),'mean_prediction':float(p[mask].mean()) if mask.any() else None,'observed_fraction':float(y[mask].mean()) if mask.any() else None})
    return {'n':n,'positives':int(y.sum()),'prevalence':float(y.mean()),'brier':brier(y,p),'auroc':auc(y,p),'average_precision':ap(y,p),'joint_calibration_intercept':float(beta[0]),'joint_calibration_slope':float(beta[1]),'calibration_iterations':it,'reliability_10_equal_width':bins,'toy_only_net_benefit':{str(th):{'model':net_benefit(y,p,th),'select_all':float(y.mean()-(1-y.mean())*th/(1-th)),'select_none':0.} for th in [.2,.5,.8]}}

def fixture_controls(spec):
    controls=[]
    y=np.array([0,0,1,1]); p=np.array([.1,.2,.8,.9])
    for name,value,expected in [('brier',brier(y,p),.025),('auroc',auc(y,p),1.),('ap',ap(y,p),1.),('net_benefit',net_benefit(y,p,.5),.5),('tied_auroc',auc(y,np.full(4,.5)),.5),('tied_ap',ap(y,np.full(4,.5)),.5),('flipped_auroc',auc(1-y,p),0.),('flipped_brier',brier(1-y,p),.725)]:
        assert abs(value-expected)<1e-12,(name,value,expected)
        controls.append({'name':name,'expected':expected,'actual':value,'passed':True})
    fixture={key:0 for key in COLUMNS}; fixture.update(row_id='synthetic-control',split='calibration',y=0)
    sealed=digest(encode([fixture])); broken=dict(fixture,y=1)
    bad_model=dict(spec['fixed_model'],intercept=0.0)
    for name,fn in [('duplicate_id_leakage',lambda:guard_rows([fixture,dict(fixture,split='evaluation')])),('label_tamper',lambda:guard_rows([broken],sealed)),('model_tamper',lambda:guard_model(bad_model,spec['fixed_model']))]:
        try: fn()
        except ValueError as e: controls.append({'name':name,'rejected':True,'message':str(e),'passed':True})
        else: raise AssertionError(name+' did not reject')
    print('CONTROL PASS: 8 known/tied/flipped metric checks; 3 intentional corruptions rejected',flush=True)
    return controls

def generate(seed,site_index,split_index,spec):
    s=spec['sites'][site_index]; n=spec['n_calibration'] if split_index==0 else spec['n_evaluation']; split='calibration' if split_index==0 else 'evaluation'
    rng=np.random.default_rng(np.random.SeedSequence([seed,site_index,split_index]))
    x1=rng.normal(size=n); x2=rng.normal(size=n); missing=rng.random(n)<s['x2_missing_probability']; u=rng.random(n)
    p_true=sigmoid(s['outcome_intercept']+x1-.5*x2); y=(u<p_true).astype(int)
    obs1=s['x1_scale']*x1; obs2=np.where(missing,0,x2)
    model=spec['fixed_model']; logit=model['intercept']+model['observed_x1_coefficient']*obs1+model['observed_x2_coefficient']*obs2
    p=sigmoid(logit); rows=[]
    for i in range(n):
        rows.append(dict(zip(COLUMNS,[f'{seed}:{site_index}:{split_index}:{i}',seed,s['name'],split,float(x1[i]),float(x2[i]),float(obs1[i]),float(obs2[i]),int(missing[i]),int(y[i]),float(p_true[i]),float(logit[i]),float(p[i]),0.])))
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--controls-only',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[4];sp=root/'runs'/ROUND/'frozen_spec.json'
    assert digest(sp.read_bytes())==SPEC_HASH,'frozen specification changed'
    spec=json.loads(sp.read_text()); controls=fixture_controls(spec)
    if args.controls_only:return
    started=time.monotonic();out=args.output;out.mkdir(parents=True,exist_ok=True);raw=out/'raw';raw.mkdir(exist_ok=True)
    all_results=[];manifest={};all_ids=set()
    for seed in spec['seeds']:
        for site_index,site in enumerate(spec['sites']):
            cal=generate(seed,site_index,0,spec);ev=generate(seed,site_index,1,spec)
            coeff,it=calibrate(cal,ev,spec['fixed_model'].copy(),spec['fixed_model'])
            rows=cal+ev;guard_rows(rows)
            ids={r['row_id'] for r in rows};assert not (all_ids & ids),'cross-run leakage';all_ids.update(ids)
            content=encode(rows);sealed=digest(content);guard_rows(rows,sealed)
            filename=f"{seed}_{site['name']}.csv";(raw/filename).write_bytes(content);manifest['raw/'+filename]=sealed
            result={'seed':seed,'site':site['name'],'n_calibration':len(cal),'n_evaluation':len(ev),'calibrator_intercept':float(coeff[0]),'calibrator_slope':float(coeff[1]),'calibrator_fit_iterations':it,'missing_calibration':sum(r['missing_x2'] for r in cal),'missing_evaluation':sum(r['missing_x2'] for r in ev),'fixed':metrics(ev,'p_fixed'),'recalibrated':metrics(ev,'p_recalibrated'),'oracle_diagnostic_only':metrics(ev,'p_true')}
            delta=np.array([(r['y']-r['p_recalibrated'])**2-(r['y']-r['p_fixed'])**2 for r in ev]);result['paired_brier_delta']=summary(delta);result['subgroups']={}
            for name,mask in [('x1_negative',np.array([r['x1']<0 for r in ev])),('x1_nonnegative',np.array([r['x1']>=0 for r in ev]))]:
                sub=[r for r,m in zip(ev,mask) if m]; sy=np.array([r['y'] for r in sub]);fp=np.array([r['p_fixed'] for r in sub]);rp=np.array([r['p_recalibrated'] for r in sub])
                result['subgroups'][name]={'n':len(sub),'positives':int(sy.sum()),'fixed_brier':brier(sy,fp),'recalibrated_brier':brier(sy,rp),'paired_brier_delta_conditional':summary(delta[mask])}
            all_results.append(result)
            print(f"{seed} {site['name']}: fixed Brier={result['fixed']['brier']:.8f}; recalibrated={result['recalibrated']['brier']:.8f}; delta={delta.mean():+.8f}",flush=True)
    aggregates=[]
    for site in spec['sites']:
        values=[r for r in all_results if r['site']==site['name']]
        ag={'site':site['name'],'primary_delta_brier':summary([r['paired_brier_delta']['mean'] for r in values],t.ppf(.975,4)),'secondary_seed_means':{key:{metric:float(np.mean([r[key][metric] for r in values])) for metric in ['brier','auroc','average_precision','joint_calibration_intercept','joint_calibration_slope']} for key in ['fixed','recalibrated','oracle_diagnostic_only']},'subgroup_delta_brier':{group:summary([r['subgroups'][group]['paired_brier_delta_conditional']['mean'] for r in values],t.ppf(.975,4)) for group in ['x1_negative','x1_nonnegative']}}
        aggregates.append(ag)
    result={'scope':'COMPLETELY SYNTHETIC METHODS DEMONSTRATION ONLY','spec_sha256':SPEC_HASH,'trials':len(all_results),'unique_synthetic_rows':len(all_ids),'controls':controls,'runs':all_results,'aggregates':aggregates,'not_run':spec['not_run'],'uncertainty_limits':spec['uncertainty_limits']}
    (out/'results.json').write_bytes(json_bytes(result));manifest['results.json']=digest((out/'results.json').read_bytes());(out/'manifest.json').write_bytes(json_bytes(manifest))
    environment={'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'machine':platform.machine(),'rng':'PCG64','cpu_only':True,'usd':0,'runtime_seconds':time.monotonic()-started,'source_sha256':digest(Path(__file__).read_bytes())}
    (out/'environment.json').write_bytes(json_bytes(environment));print(json.dumps({'aggregates':aggregates,'runtime_seconds':environment['runtime_seconds']},indent=2),flush=True)

if __name__=='__main__':main()
