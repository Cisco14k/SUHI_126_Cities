"""Estimation helpers: heat-island intensity, double machine learning with spatial cross-fitting and
block-clustered inference, mediation, sensitivity (Cinelli-Hazlett), random-effects pooling."""
import numpy as np, pandas as pd, lightgbm as lgb
from sklearn.linear_model import HuberRegressor

NP = dict(objective='regression', learning_rate=0.1, num_leaves=15, max_bin=63, min_data_in_leaf=40, feature_fraction=0.9,
          bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, verbose=-1, num_threads=1, max_cat_to_onehot=4, cat_smooth=10)
NR = 120
TERRAIN = ['elev', 'slope', 'aspect_sin', 'aspect_cos', 'elev_sd', 'dwater']
LOC = ['bin5']


def heat_island(df, k, isa_col):
    """Elevation-adjusted LST minus the rural-background median (degC). Rural background: impervious cover
    below 5% in the cell and its 1-km neighbourhood, outside the inner 30% of the radius."""
    lst = df[f'lst{k}'].values
    rural = (df[isa_col].values < 0.05) & (df['nb1k_isa'].values < 0.05) & (df['rdist'].values > 0.3) & np.isfinite(lst)
    if rural.sum() < 300:
        rural = (df[isa_col].values < 0.05) & np.isfinite(lst)
    e = df['elev'].values; er = e[rural]; lr = lst[rural]
    gam = -6.5
    if rural.sum() > 300 and np.subtract(*np.nanpercentile(er, [90, 10])) > 100:
        s = np.random.default_rng(0).choice(rural.sum(), min(rural.sum(), 5000), replace=False)
        try:
            h = HuberRegressor(max_iter=200).fit(((er[s] - np.median(er)) / 1000)[:, None], lr[s]); gam = float(np.clip(h.coef_[0], -9.8, -3.0))
        except Exception:
            gam = -6.5
    ts = lst - gam * (e - np.median(er)) / 1000
    return ts - np.nanmedian(ts[rural]), gam, int(rural.sum())


def folds_by_block(blocks, k=5, seed=0):
    ub = np.unique(blocks); rng = np.random.default_rng(seed); p = rng.permutation(len(ub))
    m = dict(zip(ub, p % k)); return np.array([m[b] for b in blocks])


def resid(y, X, folds, cat=None):
    """Cross-fitted residual of y on X (LightGBM)."""
    r = np.full(len(y), np.nan)
    for f in np.unique(folds):
        tr, te = folds != f, folds == f
        ds = lgb.Dataset(X[tr], y[tr], categorical_feature=cat or 'auto', free_raw_data=False)
        m = lgb.train(NP, ds, NR); r[te] = y[te] - m.predict(X[te])
    return r


def ols_cluster(Yt, Dt, clusters):
    """OLS of residualized outcome on residualized treatment(s), block-clustered sandwich SE."""
    D = Dt if Dt.ndim == 2 else Dt[:, None]
    A = D.T @ D; b = np.linalg.solve(A, D.T @ Yt); e = Yt - D @ b
    Ai = np.linalg.inv(A); S = np.zeros_like(A)
    for g in np.unique(clusters):
        m = clusters == g; s = D[m].T @ e[m]; S += np.outer(s, s)
    G = len(np.unique(clusters)); n, p = D.shape
    V = Ai @ S @ Ai * G / max(G - 1, 1) * (n - 1) / max(n - p, 1)
    return b, np.sqrt(np.diag(V)), e


def dml(df, y, d, W, cat=None, mediators=(), folds=None, clusters=None, Dt_given=None):
    """Partially linear DML. Returns dict with total effect of d (W only) and, if mediators given,
    direct effect and product-of-coefficient paths, all with block-clustered SE."""
    X = df[W]; folds = folds if folds is not None else folds_by_block(df['blk2'].values)
    cl = clusters if clusters is not None else df['blk2'].values
    Yt = resid(df[y].values, X, folds, cat)
    Dt = Dt_given if Dt_given is not None else resid(df[d].values, X, folds, cat)
    b, se, e = ols_cluster(Yt, Dt, cl)
    out = dict(theta=b[0], se=se[0], n=len(df), Yt=Yt, Dt=Dt, e=e,
               r2_DW=1 - np.var(Dt) / np.var(df[d].values), r2_YW=1 - np.var(Yt) / np.var(df[y].values))
    if mediators:
        Mt = np.column_stack([resid(df[m].values, X, folds, cat) for m in mediators])
        bj, sej, _ = ols_cluster(Yt, np.column_stack([Dt, Mt]), cl)
        out['direct'], out['direct_se'] = bj[0], sej[0]
        for j, m in enumerate(mediators):
            a, ase, _ = ols_cluster(Mt[:, j], Dt, cl)
            out[f'a_{m}'], out[f'b_{m}'] = a[0], bj[1 + j]
            out[f'path_{m}'] = a[0] * bj[1 + j]
            out[f'path_{m}_se'] = np.sqrt((a[0] * sej[1 + j]) ** 2 + (bj[1 + j] * ase[0]) ** 2)
        out['Mt'] = Mt
    return out


def sensitivity(Yt, Dt, e, theta, se, Yt0, Dt0, e0):
    """Cinelli & Hazlett (2020) robustness value and bias bound for an unobserved confounder as strong as the
    benchmark covariate group (location bins); *0 = residuals from nuisance models without the benchmark."""
    dof = len(Yt) - 1; t = theta / se; f = abs(t) / np.sqrt(dof)
    rv = 0.5 * (np.sqrt(f ** 4 + 4 * f ** 2) - f ** 2)
    tcrit = 1.96; fq = max(abs(t) - tcrit, 0) / np.sqrt(dof); rv_a = 0.5 * (np.sqrt(fq ** 4 + 4 * fq ** 2) - fq ** 2)
    r2dz = float(np.clip(1 - np.var(Dt) / np.var(Dt0), 0, 0.99)); r2yz = float(np.clip(1 - np.var(e) / np.var(e0), 0, 0.99))
    bias = np.sqrt(r2yz * r2dz / (1 - r2dz)) * np.std(e) / np.std(Dt)
    return dict(rv=rv, rv_alpha=rv_a, r2dz_bins=r2dz, r2yz_bins=r2yz, bias_1x=bias, theta_adj_1x=theta - np.sign(theta) * bias)


def re_pool(est, se):
    """DerSimonian-Laird random-effects pooling with 95% CI and 95% prediction interval."""
    est, se = np.asarray(est, float), np.asarray(se, float); m = np.isfinite(est) & np.isfinite(se) & (se > 0)
    est, se = est[m], se[m]; k = len(est)
    if k < 3: return dict(k=k, mu=np.nan, lo=np.nan, hi=np.nan, pi_lo=np.nan, pi_hi=np.nan, tau=np.nan, I2=np.nan)
    w = 1 / se ** 2; mu_f = (w * est).sum() / w.sum(); Q = (w * (est - mu_f) ** 2).sum()
    C = w.sum() - (w ** 2).sum() / w.sum(); tau2 = max(0, (Q - (k - 1)) / C)
    ws = 1 / (se ** 2 + tau2); mu = (ws * est).sum() / ws.sum(); sm = np.sqrt(1 / ws.sum())
    from scipy.stats import t as tdist
    tq = tdist.ppf(0.975, k - 2); pis = np.sqrt(tau2 + sm ** 2)
    return dict(k=k, mu=mu, lo=mu - 1.96 * sm, hi=mu + 1.96 * sm, pi_lo=mu - tq * pis, pi_hi=mu + tq * pis,
                tau=np.sqrt(tau2), I2=max(0, (Q - (k - 1)) / Q) if Q > 0 else 0)
