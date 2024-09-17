'use strict';
import { Row } from './Row.js';
import { AthleteInputCell } from './AthleteInputCell.js';

export class Table {
    constructor(rows) {
        this.init(rows);
    }

    init(rows) {
        this.element = document.createElement('table');

        this.thead = document.createElement('thead');
        this.element.appendChild(this.thead);

        this.tbody = document.createElement('tbody');
        this.element.appendChild(this.tbody);

        for (let row of this.rows) {
            this.tbody.appendChild(row.html());
        }

        this.rows = [];

        for (let row of rows) {
            this.appendRow(row);
        }
    }

    appendRow(row) {
        let new_row = new Row();
        new_row.appendCell(AthleteInputCell, row.athlete);
    }

    html() {
        return this.element;
    }
}
