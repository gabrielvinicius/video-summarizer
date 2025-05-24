export type Video = {
  id: string;
  user_id: string;
  status: "UPLOADED" | "PROCESSING" | "COMPLETED" | "FAILED";
  created_at: string;
  transcription_id?: string;
  summary_id?: string;
};

export type User = {
  id: string;
  email: string;
  created_at: string;
  is_active: boolean;
};