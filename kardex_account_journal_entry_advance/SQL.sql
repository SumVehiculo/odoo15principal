

CREATE OR REPLACE VIEW vst_property_stock_valuation_account AS
SELECT
CASE 
	WHEN res_id IS NOT NULL THEN SUBSTRING (res_id,'([0-9]{1,10})')::integer
	ELSE NULL
END AS category_id,
res_id,
CASE 
	WHEN value_reference IS NOT NULL THEN SUBSTRING (value_reference,'([0-9]{1,20})')::integer
	ELSE NULL
END AS account_id,
value_reference,
company_id
FROM ir_property WHERE name = 'property_stock_valuation_account_id';

CREATE OR REPLACE VIEW vst_property_stock_account_input AS
SELECT
CASE 
	WHEN res_id IS NOT NULL THEN SUBSTRING (res_id,'([0-9]{1,10})')::integer
	ELSE NULL
END AS category_id,
res_id,
CASE 
	WHEN value_reference IS NOT NULL THEN SUBSTRING (value_reference,'([0-9]{1,20})')::integer
	ELSE NULL
END AS account_id,
value_reference,
company_id
FROM ir_property WHERE name = 'property_stock_account_input_categ_id';

CREATE OR REPLACE VIEW vst_property_stock_account_output AS
SELECT
CASE 
	WHEN res_id IS NOT NULL THEN SUBSTRING (res_id,'([0-9]{1,10})')::integer
	ELSE NULL
END AS category_id,
res_id,
CASE 
	WHEN value_reference IS NOT NULL THEN SUBSTRING (value_reference,'([0-9]{1,20})')::integer
	ELSE NULL
END AS account_id,
value_reference,
company_id
FROM ir_property WHERE name = 'property_stock_account_output_categ_id';