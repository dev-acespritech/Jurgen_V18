/** @odoo-module **/

export const A4_REPORT_NAME = "pos_print_format.report_pos_order_a4";
/**
 * Fetch the A4 PDF of a synced order and send it to the browser's print function
 * through a hidden iframe.
 */
export async function printA4Pdf(orderId) {
    const response = await fetch(`/report/pdf/${A4_REPORT_NAME}/${orderId}`, {
        credentials: "same-origin",
    });
    const contentType = response.headers.get("content-type") || "";
    if (!response.ok || !contentType.includes("pdf")) {
        throw new Error(`A4 report request failed (HTTP ${response.status})`);
    }
    const blobUrl = URL.createObjectURL(
        new Blob([await response.blob()], { type: "application/pdf" })
    );
    return new Promise((resolve) => {
        const iframe = document.createElement("iframe");
        iframe.style.cssText =
            "position:fixed;right:0;bottom:0;width:1px;height:1px;border:0;opacity:0;";
        iframe.onload = () => {
            try {
                iframe.contentWindow.focus();
                iframe.contentWindow.print();
            } catch {
                window.open(blobUrl, "_blank");
            }
            setTimeout(() => {
                iframe.remove();
                URL.revokeObjectURL(blobUrl);
            }, 60000);
            resolve(true);
        };
        iframe.src = blobUrl;
        document.body.appendChild(iframe);
    });
}