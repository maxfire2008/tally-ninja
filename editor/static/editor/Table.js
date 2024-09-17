"use strict";
import { Row } from "./Row.js";
import { AthleteInputCell } from "./AthleteInputCell.js";

export class Table {
    constructor(rows, type) {
        this.init(rows, type);
    }

    init(rows, type) {
        this.columns = [];
        if (type === 'race') {
            this.columns.push(
                {
                    "type": AthleteInputCell,
                    "key": "athlete",
                }
            )
        }
        this.rows = [];

        for (let row of rows) {
            this.appendRow(row);
        }

        this.element = document.createElement("table");

        this.thead = document.createElement("thead");
        this.element.appendChild(this.thead);

        this.tbody = document.createElement("tbody");
        this.element.appendChild(this.tbody);

        for (let row of this.rows) {
            this.tbody.appendChild(row.html());
        }
    }

    appendRow(row) {
        let new_row = new Row();
        for (let column of this.columns) {
            new_row.appendCell(column.type, row[column.key], column.key);
        }
        this.rows.push(new_row);
    }

    html() {
        return this.element;
    }

    value() {
        let table = [];
        for (let row of this.rows) {
            table.push(row.value());
        }
        return table;
    }
}
