import api from './api';

export interface ReportPage<T = Record<string, any>> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  summary: Record<string, number>;
}

export const reportsService = {
  list: (report: string, params: Record<string, any>) => api.get<ReportPage>(`/reports/${report}`, { params }),
  financeSummary: () => api.get<Record<string, number>>('/reports/finance-summary'),
  licenseSummary: () => api.get<Record<string, number>>('/reports/licenses'),
  export: (report: string, params: Record<string, any>) => api.get(`/reports/${report}`, { params: { ...params, export: true }, responseType: 'blob' }),
};
