"use strict";
import { Row } from "./Row.js";
import { HeaderTextCell } from "./HeaderTextCell.js";
import { NumberInputCell } from "./NumberInputCell.js";
import { AthleteInputCell } from "./AthleteInputCell.js";

export class Table {
    constructor(rows, type, config) {
        this.init(rows, type, config);
    }

    init(rows, type, config) {
        this.config = config;
        this.columns = [];
        if (type === 'race') {
            this.columns.push(
                {
                    "type": NumberInputCell,
                    "key": "heat",
                    "heading": "Heat",
                }
            )
            this.columns.push(
                {
                    "type": NumberInputCell,
                    "key": "lane",
                    "heading": "Lane",
                }
            )
            this.columns.push(
                {
                    "type": AthleteInputCell,
                    "key": "athlete",
                    "heading": "Athlete",
                }
            )
        }

        this.element = document.createElement("table");

        this.thead = document.createElement("thead");

        this.header = new Row();
        for (let column of this.columns) {
            this.header.appendCell(HeaderTextCell, column.heading, column.key, this.config);
        }
        this.thead.appendChild(this.header.html());

        this.element.appendChild(this.thead);

        this.tbody = document.createElement("tbody");
        this.element.appendChild(this.tbody);

        this.rows = [];

        for (let row of rows) {
            this.appendRow(row);
        }

        // register key event listener
        document.addEventListener('keydown', this.keydown);
    }

    appendRow(row) {
        let new_row = new Row();
        for (let column of this.columns) {
            new_row.appendCell(column.type, row[column.key], column.key, this.config);
        }
        this.rows.push(new_row);
        this.tbody.appendChild(new_row.html());
    }

    keydown(event) {
        console.log(event);
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
