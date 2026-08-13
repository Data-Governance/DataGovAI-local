export const logger = {
  info: (obj: unknown, msg?: string) =>
    console.info(msg ?? "", typeof obj === "string" ? obj : obj),
  warn: (obj: unknown, msg?: string) =>
    console.warn(msg ?? "", typeof obj === "string" ? obj : obj),
  error: (obj: unknown, msg?: string) =>
    console.error(msg ?? "", typeof obj === "string" ? obj : obj),
};
