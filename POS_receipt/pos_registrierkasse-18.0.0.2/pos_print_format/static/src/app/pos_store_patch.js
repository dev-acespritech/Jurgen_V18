/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { printA4Pdf } from "./a4_print_utils";

patch(PosStore.prototype, {
    async printReceipt({
        basic = false,
        order = this.get_order(),
        printBillActionTriggered = false,
    } = {}) {
        // A4 only for final receipts of orders already saved on the server
        const useA4 =
            this.config.enable_a4_printing &&
            !basic &&
            !printBillActionTriggered &&
            typeof order?.id === "number";
        if (!useA4) {
            return super.printReceipt(...arguments);
        }
        try {
            await printA4Pdf(order.id);
        } catch (error) {
            this.notification.add(_t("A4 printing failed. Please try again from the receipt screen."), {
                type: "danger",
            });
            return false;
        }
        order.nb_print += 1;
        await this.data.write("pos.order", [order.id], { nb_print: order.nb_print });
        return true;
    },
});