import {
  ApiError,
  type ApiErrorCode,
  CreateRoomResponse,
  type JoinRequest,
  JoinResponse,
  RoomInfo,
} from "@lt/contracts";

export class RequestError extends Error {
  constructor(public code: ApiErrorCode) {
    super(code);
  }
}

type Schema<T> = { parse: (data: unknown) => T };

async function call<T>(schema: Schema<T>, path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { "content-type": "application/json", ...init?.headers },
    });
  } catch {
    throw new RequestError("internal");
  }
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const err = ApiError.safeParse(body);
    throw new RequestError(err.success ? err.data.error : "internal");
  }
  return schema.parse(body);
}

export const api = {
  createRoom: () => call(CreateRoomResponse, "/api/rooms", { method: "POST" }),
  room: (id: string) => call(RoomInfo, `/api/rooms/${id}`),
  join: (id: string, req: JoinRequest) =>
    call(JoinResponse, `/api/rooms/${id}/join`, { method: "POST", body: JSON.stringify(req) }),
};
