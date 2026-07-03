import api from './api';

export const locationService = {
  getStates: () => api.get('/masters/states'),
  getDistricts: (stateId: number) => api.get(`/masters/districts?state_id=${stateId}`),
  getBlocks: (districtId: number) => api.get(`/masters/blocks?district_id=${districtId}`),
};