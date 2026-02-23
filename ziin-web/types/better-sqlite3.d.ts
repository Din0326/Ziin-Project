declare module "better-sqlite3" {
  type RunResult = { changes: number; lastInsertRowid: number | bigint };

  interface Statement {
    run(...params: unknown[]): RunResult;
    get(...params: unknown[]): unknown;
    all(...params: unknown[]): unknown[];
  }

  interface Transaction<TArgs extends unknown[]> {
    (...args: TArgs): void;
  }

  class Database {
    constructor(filename: string);
    pragma(source: string): void;
    exec(source: string): void;
    prepare(source: string): Statement;
    transaction<TArgs extends unknown[]>(fn: (...args: TArgs) => void): Transaction<TArgs>;
  }

  namespace Database {
    export { Database };
  }

  export default Database;
}
