# Supplementary Software: surface heat cost of urban sealing, 126 city-regions (1985–2025)

Run order (Python 3.13; numpy, pandas, xarray, rasterio, pystac-client, planetary-computer, lightgbm, scikit-learn, scipy, h5py, fsspec, matplotlib, python-docx). All data are read from the Microsoft Planetary Computer.

1. cities.py; terraclimate.py (+ tc_fix.py) – city table, climate boxes
2. static126.py; lcmap.py – WorldCover, DEM, GlobPOP, ESA CCI; LCMAP (US)
3. landsat126.py @list – warm-season Landsat composites, four epochs (lsread.py)
4. cells.py; backcast.py; validate_bc.py – cell tables, back-cast, validation
5. cmip6.py; climate.py cmip6 – climate descriptors and NEX-GDDP-CMIP6 deltas
6. city_dml.py; city_extra.py – within-city estimands and round-3 checks (lagged outcome, spillover, concordant dating)
7. transfer.py build|six|continent zone|merge; transfer_nl.py – transfer tests, conformal intervals, nonlinear R-learner
8. simulate.py; project.py – simulations; projections to 2100
9. summarize.py; summarize2.py; figs.py; edfigs.py; build_ms2.py; build_si2.py; build_resp3.py

common.py holds paths and the 120-m grid; est.py the estimators; figstyle.py the NPG palette.

Round 4: city_extra2.py (2-km location bins), summarize3.py (independent benchmark, Europe), build_ms3.py, build_si3.py, build_resp4.py.
Round 5: city_extra3.py (CCI-dosed dating, lagged design in vegetated cells), summarize4.py, build_ms4.py, build_si4.py, build_resp5.py.
