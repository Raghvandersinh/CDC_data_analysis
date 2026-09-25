DESCRIBE sm_db.stroke_mortality;

SELECT DISTINCT race FROM sm_db.stroke_mortality;

SELECT DISTINCT sex FROM sm_db.stroke_mortality;

SELECT DISTINCT location, geo_level FROM sm_db.stroke_mortality;

SELECT DISTINCT state FROM sm_db.stroke_mortality;

SELECT DISTINCT icd_class FROM sm_db.stroke_mortality;

SELECT DISTINCT geo_level FROM sm_db.stroke_mortality;

SELECT DISTINCT topic FROM sm_db.stroke_mortality;

SELECT DISTINCT state FROM sm_db.stroke_mortality;

SELECT COUNT(state) FROM sm_db.stroke_mortality
where state = 'NJ';