/** @odoo-module **/

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";
import { A4ReceiptPreview } from "./a4_receipt_preview";

patch(ReceiptScreen, {
    components: { ...ReceiptScreen.components, A4ReceiptPreview },
});

patch(ReceiptScreen.prototype, {
    get showA4Preview() {
        return (
            Boolean(this.pos.config.enable_a4_printing) &&
            typeof this.currentOrder?.id === "number"
        );
    },
});