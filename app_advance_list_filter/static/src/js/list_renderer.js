/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

console.log("🔥 ADVANCE COLUMN SEARCH WITH DATE RANGE LOADED 🔥");

// UI field → real stored field
const FIELD_MAP = {
    expected_date: "commitment_date",
};

patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        this.columnSearchValues = {};
        this.baseDomain = [];
    },


    willUpdateProps() {
        // 🔥 ALWAYS sync with search bar domain
        if (this.props.list?.searchModel) {
            this.baseDomain = this.props.list.searchModel.getDomain() || [];
        }
    },



    onColumnSearchInput(ev, uiField) {
        const value = ev.target.value;

        if (value) {
            this.columnSearchValues[uiField] = value;
        } else {
            delete this.columnSearchValues[uiField];
        }

        const columnDomain = [];
        const fields = this.props.list.fields || {};

        const toUTC = (d) =>
            d.toISOString().slice(0, 19).replace("T", " ");

        const dateGroups = {};

        for (const [key, v] of Object.entries(this.columnSearchValues)) {
            const baseField = key.replace("__from", "").replace("__to", "");
            const realField = FIELD_MAP[baseField] || baseField;
            const fieldType = fields[baseField]?.type;

            // 🟢 DATE / DATETIME
            if (["date", "datetime"].includes(fieldType)) {
                if (!dateGroups[baseField]) {
                    dateGroups[baseField] = {
                        realField,
                        fieldType,
                        from: null,
                        to: null,
                    };
                }
                if (key.endsWith("__from")) dateGroups[baseField].from = v;
                if (key.endsWith("__to")) dateGroups[baseField].to = v;
            }

            // 🟢 OTHER FIELDS (TEXT, MANY2ONE, etc.)
            else {
                columnDomain.push([realField, "ilike", v]);
            }
        }

        // 🔹 Date domain build
        for (const group of Object.values(dateGroups)) {
            const { realField, fieldType, from, to } = group;

            if (fieldType === "date") {
                if (from && to) {
                    columnDomain.push([realField, ">=", from]);
                    columnDomain.push([realField, "<=", to]);
                } else if (from) {
                    columnDomain.push([realField, "=", from]);
                }
            } else if (fieldType === "datetime") {
                if (from && to) {
                    columnDomain.push([
                        realField,
                        ">=",
                        toUTC(new Date(from + "T00:00:00")),
                    ]);
                    columnDomain.push([
                        realField,
                        "<=",
                        toUTC(new Date(to + "T23:59:59")),
                    ]);
                } else if (from) {
                    columnDomain.push([
                        realField,
                        ">=",
                        toUTC(new Date(from + "T00:00:00")),
                    ]);
                    columnDomain.push([
                        realField,
                        "<=",
                        toUTC(new Date(from + "T23:59:59")),
                    ]);
                }
            }
        }

        const currentDomain = this.baseDomain;

        this.props.list.load({
            domain: [...this.baseDomain, ...columnDomain],
            offset: 0,
            forceSearchCount: true,
        });


    },

});
