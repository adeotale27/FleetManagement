export type User = {
  id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  tenant_id?: string | null;
  tenant?: Record<string, unknown> | null;
  support?: boolean;
};

export type PageResult<T> = {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
};

export type ApiError = { success: false; error: { code: string; message: string } };
