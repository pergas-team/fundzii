export type WorkflowStep = {
  id: number;
  key: string;
  title: string;
  order?: number;
};

export type RequestHistoryItem = {
  id: number;
  from_status?: string | null;
  to_status: string;
  changed_by?: string | null;
  note?: string;
  created_at: string;
};
