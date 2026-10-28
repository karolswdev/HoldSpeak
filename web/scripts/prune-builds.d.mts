export declare const KEEP_BUILDS: number;
export declare const MANIFEST: string;
export interface KeptBuild {
  build_id: string;
  built_at: string;
  assets: string[];
}
export declare function readBuilds(outDir: string): KeptBuild[];
export declare function indexAssets(outDir: string): string[];
export declare function pruneAssets(outDir: string, builds?: KeptBuild[]): string[];
export declare function recordBuild(
  outDir: string,
  assets: string[],
  options?: { buildId?: string; keep?: number; now?: Date },
): { builds: KeptBuild[]; removed: string[] };
