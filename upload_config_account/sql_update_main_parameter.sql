DROP FUNCTION IF EXISTS public.update_main_parameter(integer,character varying) CASCADE;

CREATE OR REPLACE FUNCTION public.update_main_parameter(
    company_id integer,
	dir_file character varying,
    parameter_id integer
) RETURNS BOOLEAN LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
update account_main_parameter set 
supplier_advance_account_nc=(select id from account_account where code='4220001' and account_account.company_id=$1 limit 1),
supplier_advance_account_fc=(select id from account_account where code='4220002' and account_account.company_id=$1 limit 1),
customer_advance_account_nc=(select id from account_account where code='1220001' and account_account.company_id=$1 limit 1),
customer_advance_account_fc=(select id from account_account where code='1220002' and account_account.company_id=$1 limit 1),
detractions_account=(select id from account_account where code='4250000' and account_account.company_id=$1 limit 1),
customer_account_detractions=(select id from account_account where code='1212500' and account_account.company_id=$1 limit 1),
free_transer_account_id=(select id from account_account where code='6411000' and account_account.company_id=$1 limit 1),
destination_journal=(select id from account_journal where code='AUT' and type='general' and account_journal.company_id=$1 limit 1),
detraction_journal=(select id from account_journal where code='PDET' and type='general' and account_journal.company_id=$1 limit 1),
credit_journal=(select id from account_journal where code='ANC' and type='general' and account_journal.company_id=$1 limit 1),
free_transfer_journal_id=(select id from account_journal where code='TRG' and type='general' and account_journal.company_id=$1 limit 1),
dt_national_credit_note=(select id from l10n_latam_document_type where l10n_latam_document_type.code='07' limit 1),
td_recibos_hon=(select id from l10n_latam_document_type where l10n_latam_document_type.code='02' limit 1),
exportation_document=(select id from l10n_latam_document_type where l10n_latam_document_type.code='50' limit 1),
proff_payment_wa=(select id from l10n_latam_document_type where l10n_latam_document_type.code='91' limit 1),
debit_note_wa=(select id from l10n_latam_document_type where l10n_latam_document_type.code='98' limit 1),
credit_note_wa=(select id from l10n_latam_document_type where l10n_latam_document_type.code='97' limit 1),
account_plan_code='01',
cash_account_prefix='''101'',''102'',''103'',''105''',
bank_account_prefix='''104'',''106'',''107''',
cancelation_partner=(select id from res_partner where name='DOCUMENTOS ANULADOS' and vat='00000000000' limit 1),
sale_ticket_partner=(select id from res_partner where name='BOLETAS DE VENTAS' and vat='00000000002' limit 1),
dir_create_file=$2,
tax_account=(select id from account_account_tag where account_account_tag.name='PER-C' limit 1),
dt_perception=(select id from l10n_latam_document_type where l10n_latam_document_type.code='00' limit 1),
customer_letter_account_nc=(select id from account_account where code='1232001' and account_account.company_id=$1 limit 1),
customer_letter_account_fc=(select id from account_account where code='1232002' and account_account.company_id=$1 limit 1),
rounding_gain_account=(select id from account_account where code='7599000' and account_account.company_id=$1 limit 1),
rounding_loss_account=(select id from account_account where code='6592000' and account_account.company_id=$1 limit 1),
supplier_letter_account_nc=(select id from account_account where code='4230001' and account_account.company_id=$1 limit 1),
supplier_letter_account_fc=(select id from account_account where code='4230002' and account_account.company_id=$1 limit 1),
balance_sheet_account=(select id from account_account where code='8910000' and account_account.company_id=$1 limit 1),
lost_sheet_account=(select id from account_account where code='8920000' and account_account.company_id=$1 limit 1),
profit_result_account=(select id from account_account where code='5911000' and account_account.company_id=$1 limit 1),
lost_result_account=(select id from account_account where code='5921000' and account_account.company_id=$1 limit 1)
--Etiqueta para Kardex
where account_main_parameter.id = $3;
RETURN FOUND;
END;
$$;
