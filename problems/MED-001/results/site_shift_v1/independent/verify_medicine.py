"""Independent raw-data replay; no imports from author implementation.
Usage: python verify_medicine.py path/to/site_shift_v1 > review.json
Requires NumPy/SciPy. Review written after author results were visible, not blind.
"""
import csv,json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.special import expit
from scipy.optimize import least_squares
from scipy.stats import t
p=Path(sys.argv[1]); report=json.loads((p/'results.json').read_text()); gaps=[]; counts=0; allids=set(); deltas={}; hashes={}
def check(a,b,tol=1e-10):
 g=float(np.max(np.abs(np.asarray(a)-np.asarray(b)))); gaps.append(g); assert g<=tol,(g,tol)
def fit(z,y):
 X=np.column_stack([np.ones(len(z)),z]); f=lambda b:X.T@(expit(X@b)-y)
 r=least_squares(f,[0.,1.],xtol=1e-14,ftol=1e-14,gtol=1e-14,max_nfev=1000)
 assert r.success and np.max(np.abs(f(r.x)))<1e-8
 return r.x
for run in report['runs']:
 seed,site=run['seed'],run['site']; si=['A_reference','B_intercept','C_measurement'].index(site)
 fn=p/'raw'/f'{seed}_{site}.csv'; hashes[fn.name]=hashlib.sha256(fn.read_bytes()).hexdigest(); rows=list(csv.DictReader(fn.open())); counts+=len(rows)
 for row in rows:
  assert row['row_id'] not in allids; allids.add(row['row_id'])
 splits=[]
 for split_index,(split,n) in enumerate([('calibration',256),('evaluation',512)]):
  rr=[r for r in rows if r['split']==split]; assert len(rr)==n
  a={k:np.array([float(r[k]) for r in rr]) for k in rr[0] if k not in ['row_id','site','split']}
  rng=np.random.default_rng(np.random.SeedSequence([seed,si,split_index])); x1=rng.normal(size=n); x2=rng.normal(size=n); mu=rng.random(n); yu=rng.random(n)
  intercept=[-.5,.8,-.5][si]; scale=[1,1,2][si]; missing=mu<([0,0,.1][si]); ox2=np.where(missing,0,x2)
  truth=expit(intercept+x1-.5*x2); z=-.5+scale*x1-.5*ox2
  for key,val in [('x1',x1),('x2',x2),('observed_x1',scale*x1),('observed_x2',ox2),('missing_x2',missing),('y',yu<truth),('p_true',truth),('fixed_logit',z),('p_fixed',expit(z))]:check(a[key],val)
  splits.append(a)
 ca,ev=splits; coeff=fit(ca['fixed_logit'],ca['y']);check(coeff,[run['calibrator_intercept'],run['calibrator_slope']],1e-8)
 for a in splits:check(a['p_recalibrated'],expit(coeff[0]+coeff[1]*a['fixed_logit']),1e-9)
 y=ev['y']; ds=(ev['p_recalibrated']-y)**2-(ev['p_fixed']-y)**2; deltas.setdefault(site,[]).append(float(ds.mean())); check(ds.mean(),run['paired_brier_delta']['mean'])
 for label,key in [('fixed','p_fixed'),('recalibrated','p_recalibrated'),('oracle_diagnostic_only','p_true')]:
  pr=ev[key]; out=run[label];check(np.mean((pr-y)**2),out['brier']); pair=pr[y==1,None]-pr[y==0]; auc=np.mean((pair>0)+.5*(pair==0));check(auc,out['auroc'])
  ap=0.
  for v in np.unique(pr):
   mask=pr>=v; ap+=np.sum(y[pr==v])/np.sum(y)*np.mean(y[mask])
  check(ap,out['average_precision']); cb=fit(np.log(pr/(1-pr)),y);check(cb,[out['joint_calibration_intercept'],out['joint_calibration_slope']],1e-8)
  for b in out['reliability_10_equal_width']:
   mask=(pr>=b['lower'])&(pr<b['upper'] if b['upper']<1 else pr<=1);check(mask.sum(),b['n'])
   if mask.any():check(pr[mask].mean(),b['mean_prediction']);check(y[mask].mean(),b['observed_fraction'])
  for threshold,v in out['toy_only_net_benefit'].items():
   th=float(threshold); selected=pr>=th; nb=(sum(selected&(y==1))-sum(selected&(y==0))*th/(1-th))/len(y);check(nb,v['model'])
for a in report['aggregates']:
 d=np.array(deltas[a['site']]); se=d.std(ddof=1)/np.sqrt(5); ci=d.mean()+np.array([-1,1])*t.ppf(.975,4)*se
 check(d.mean(),a['primary_delta_brier']['mean']);check(se,a['primary_delta_brier']['standard_error']);check(ci,a['primary_delta_brier']['interval95'],1e-10)
assert counts==11520 and len(report['runs'])==15
print(json.dumps({'status':'PASS','scope':'Independent raw DGP replay, calibration-only alternate least-squares score solver, Brier/pairwise AUROC/grouped AP/calibration/reliability/toy net benefit, primary seed-t intervals','not_verified':['Clinical validity or utility','Prospective performance','Author corruption-control implementation','Conditional row confidence intervals and subgroup summaries'], 'trials':15,'rows':counts,'checks':len(gaps),'maximum_numeric_gap':max(gaps),'raw_sha256':hashes,'primary_delta_brier':deltas,'limits':'Synthetic data only; reviewer saw results; same NumPy random generator, distinct evaluator code; no author imports.'},indent=2))
