import { db } from "./db";

/** The JSON body /api/download-pdf returns when it cannot resolve a PDF. */
interface DownloadRefusal {
  message?: string;
  landingUrl?: string;
}

export interface DownloadProgressCallback {
  (status: "starting" | "resolving" | "saving" | "success" | "paywalled" | "error", details?: string): void;
}

export async function fetchAndStorePaperPdf(
  params: {
    doi?: string;
    title: string;
    pdfUrl?: string;
    sourceId?: string;
    notebookId?: string;
  },
  onProgress?: DownloadProgressCallback
): Promise<{ success: boolean; blob?: Blob; sourceName?: string; landingUrl?: string }> {
  try {
    onProgress?.("resolving", "Running Vellum Multi-Tier Protocol (Direct OA, Springer/Nature, Unpaywall, Semantic Scholar, Europe PMC, Mirrors)...");

    const response = await fetch("/api/download-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doi: params.doi,
        title: params.title,
        pdfUrl: params.pdfUrl,
      }),
    });

    if (response.ok && response.headers.get("content-type")?.includes("application/pdf")) {
      onProgress?.("saving", "Validating PDF binary signature and writing to Local IndexedDB Vault...");
      const blob = await response.blob();
      const resolvedSource = response.headers.get("x-vellum-resolved-source") || "Academic Protocol";

      // If sourceId is provided, persist blob to IndexedDB
      if (params.sourceId) {
        await db.sources.update(params.sourceId, {
          pdfBlob: blob,
          sizeBytes: blob.size,
          status: "ready",
        });
      }

      onProgress?.("success", `Retrieved via ${resolvedSource} (${(blob.size / 1024 / 1024).toFixed(2)} MB)`);
      return { success: true, blob, sourceName: resolvedSource };
    } else {
      const data = (await response.json()) as DownloadRefusal;
      onProgress?.("paywalled", data.message || "Paywalled by publisher");
      return { success: false, landingUrl: data.landingUrl };
    }
  } catch (err) {
    console.error("PDF download client error:", err);
    onProgress?.("error", err instanceof Error ? err.message : "Network error");
    return { success: false };
  }
}

export function triggerBrowserFileDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.endsWith(".pdf") ? filename : `${filename}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}
