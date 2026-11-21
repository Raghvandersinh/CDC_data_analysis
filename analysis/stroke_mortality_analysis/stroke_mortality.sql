COPY(
SELECT * FROM sm_db.stroke_mortality
WHERE state = 'NJ'
) TO 'data/NJ_stroke_mortality.csv' (HEADER, DELIMITER ',');

