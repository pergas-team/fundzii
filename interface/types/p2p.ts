export type P2PField = {
  label: string;
  value: string | number | string[];
  type: string;
};

export type PublicP2PRequest = {
  id: number;
  ref: string;
  current_status: string;
  submitted_at: string;
  fields: Record<string, P2PField>;
};

export type PublicP2PResponse = {
  count: number;
  results: PublicP2PRequest[];
};
