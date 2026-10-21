/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { A4_REPORT_NAME } from "./a4_print_utils";

const A4_WIDTH_PX = 794;
const A4_HEIGHT_PX = 1123;

export class A4ReceiptPreview extends Component {
    static template = "pos_print_format.A4ReceiptPreview";
    static props = { orderId: Number };

    setup() {
        this.wrapperRef = useRef("wrapper");
        this.state = useState({ scale: 0.6 });
        onMounted(() => {
            this.observer = new ResizeObserver(() => this.updateScale());
            this.observer.observe(this.wrapperRef.el);
            this.updateScale();
        });
        onWillUnmount(() => this.observer?.disconnect());
    }

    get src() {return `/report/html/${A4_REPORT_NAME}/${this.props.orderId}`;}

    get wrapperStyle() {
        const height = Math.ceil(A4_HEIGHT_PX * this.state.scale);
        return `width:100%; height:${height}px; overflow:hidden; position:relative;`;
    }

    get iframeStyle() {
        return (
            `border:0; width:${A4_WIDTH_PX}px; height:${A4_HEIGHT_PX}px; ` +
            `transform-origin:0 0; transform:scale(${this.state.scale});`
        );
    }

    updateScale() {
        const width = this.wrapperRef.el?.clientWidth;
        if (width) {
            this.state.scale = width / A4_WIDTH_PX;
        }
    }
}