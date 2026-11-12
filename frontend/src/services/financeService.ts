import api from './api';
export interface FinanceAccount { id:number; organization_id:number; account_code:string; account_name:string; account_type:string; account_group:string; account_subtype:string|null; system_key:string|null; is_active:boolean }
export interface FinanceYear { id:number; organization_id:number; name:string; start_date:string; end_date:string; is_current:boolean; is_locked:boolean; locked_at:string|null }
export interface JournalLine { id?:number; account_id:number; debit:number; credit:number; party_type:'FARMER'|'CUSTOMER'|null; party_id:number|null; line_narration?:string|null }
export interface Journal { id:number; organization_id:number; journal_no:string; entry_date:string; financial_year_id:number; narration:string; source_type:string; source_id:number|null; status:string; created_at:string; lines:JournalLine[] }
export const financeService = {
 setup:()=>api.post('/finance/setup'), setupStatus:()=>api.get('/finance/setup/status'),
 years:()=>api.get<FinanceYear[]>('/finance/years'), createYear:(data:Partial<FinanceYear>)=>api.post('/finance/years',data), setCurrent:(id:number)=>api.patch(`/finance/years/${id}/current`), setLocked:(id:number,locked:boolean)=>api.patch(`/finance/years/${id}/lock`,null,{params:{locked}}),
 accounts:()=>api.get<FinanceAccount[]>('/finance/accounts'), createAccount:(data:Partial<FinanceAccount>)=>api.post('/finance/accounts',data), updateAccount:(id:number,data:Partial<FinanceAccount>)=>api.put(`/finance/accounts/${id}`,data), setAccountActive:(id:number,is_active:boolean)=>api.patch(`/finance/accounts/${id}/status`,{is_active}),
 journals:()=>api.get<Journal[]>('/finance/journals'), createJournal:(data:unknown)=>api.post('/finance/journals',data), voidJournal:(id:number,void_reason:string)=>api.patch(`/finance/journals/${id}/void`,{void_reason}), ledger:(params:unknown)=>api.get('/finance/reports/general-ledger',{params}), trialBalance:(params:unknown)=>api.get('/finance/reports/trial-balance',{params}),
};
