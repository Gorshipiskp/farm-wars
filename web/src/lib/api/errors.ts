export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly httpStatus = 0,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
