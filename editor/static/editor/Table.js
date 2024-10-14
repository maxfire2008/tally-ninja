"use strict";
import { Row } from "./Row.js";
import { HeaderTextCell } from "./HeaderTextCell.js";
import { NumberInputCell } from "./NumberInputCell.js";
import { DurationInputCell } from "./DurationInputCell.js";
import { AthleteInputCell } from "./AthleteInputCell.js";
import { HighJumpInputCell } from "./HighJumpInputCell.js";
import { DeleteButtonCell } from "./DeleteButtonCell.js";

export class Table {
    constructor(rows, type, doc_type, config) {
        this.init(rows, type, doc_type, config);
    }

    init(rows, type, doc_type, config) {
        this.config = config;
        this.columns = [];
        console.log('type', type);
        console.log('doc_type', doc_type);

        this.element = document.createElement("table");

        this.thead = document.createElement("thead");

        this.header = new Row();
        this.thead.appendChild(this.header.element);

        this.element.appendChild(this.thead);

        this.tbody = document.createElement("tbody");
        this.element.appendChild(this.tbody);

        this.rows = [];

        for (let row of rows) {
            this.appendRow(row);
        }

        if (type === 'race' && doc_type === 'results') {
            this.appendColumn(
                {
                    "type": NumberInputCell,
                    "key": "heat",
                    "heading": "Heat",
                }
            )
            this.appendColumn(
                {
                    "type": NumberInputCell,
                    "key": "lane",
                    "heading": "Lane",
                }
            )
            this.appendColumn(
                {
                    "type": AthleteInputCell,
                    "key": "athlete",
                    "heading": "Athlete",
                }
            )
        } else if (type === 'race' && doc_type === 'times') {
            this.appendColumn(
                {
                    "type": NumberInputCell,
                    "key": "heat",
                    "heading": "Heat",
                }
            )
            this.appendColumn(
                {
                    "type": NumberInputCell,
                    "key": "lane",
                    "heading": "Lane",
                }
            )
            this.appendColumn(
                {
                    "type": DurationInputCell,
                    "key": "time",
                    "heading": "Time",
                }
            )
        } else if (type === 'high_jump') {
            this.appendColumn(
                {
                    "type": AthleteInputCell,
                    "key": "athlete",
                    "heading": "Athlete",
                }
            )
            // iterate all the heights in the data and add a column for each
            let heights = new Set();
            for (let row of rows) {
                console.log(row.heights);
                for (let height of Object.keys(row.heights)) {
                    heights.add(height);
                }
            }
            heights = Array.from(heights).sort();
            for (let height of heights) {
                this.appendColumn(
                    {
                        "type": HighJumpInputCell,
                        "key": "heights." + height,
                        "heading": height,
                    }
                )
            }
        }

        this.appendColumn(
            {
                "type": DeleteButtonCell,
                "key": "!delete",
                "heading": "",
            }
        )

        // register key event listener
        this.keydown = this.keydown.bind(this);
        document.addEventListener('keydown', this.keydown);
    }

    appendColumn(column) {
        console.log('column', column);
        this.header.appendCell(HeaderTextCell, column.heading, column.key, this.config);
        this.columns.push(column);
        for (let row of this.rows) {
            // get the value of the cell
            row.appendCell(column.type, null, column.key, this.config);
        }
    }

    appendRow(row) {
        let new_row = new Row();
        for (let column of this.columns) {
            const key = column.key.split('.');
            let value = row;
            while (key.length > 0) {
                value = value[key.shift()];
            }
            new_row.appendCell(column.type, value, column.key, this.config);
        }
        if (new_row.onAdd !== undefined) {
            new_row.onAdd();
        }
        this.rows.push(new_row);
        this.tbody.appendChild(new_row.element);
    }

    keydown(event) {
        // Enter will go to the next row but the same cell
        if (event.key === 'Enter') {
            event.preventDefault();
            // get the target of the key event and get it's row
            let target = event.target;
            let row = target.parentElement;
            while (row.tagName !== 'TR') {
                row = row.parentElement;
                if (row === this.tbody) {
                    throw new Error('Could not find row');
                }
            }

            // get the index of the row
            let index = Array.from(this.tbody.children).indexOf(row);

            // get the index of the object within the row (note: it may be nested)
            let cell = target;
            while (cell.tagName !== 'TD') {
                cell = cell.parentElement;
                if (cell === row) {
                    throw new Error('Could not find cell');
                }
            }
            let cell_index = Array.from(row.children).indexOf(cell);

            // get the next row
            // if shift
            let next_row;
            if (event.shiftKey) {
                next_row = this.tbody.children[index - 1];
                if (next_row === undefined) {
                    // wrap around to the bottom
                    next_row = this.tbody.children[this.tbody.children.length - 1];
                }
            } else {
                next_row = this.tbody.children[index + 1];
                if (next_row === undefined) {
                    // wrap around to the top
                    next_row = this.tbody.children[0];
                }
            }

            // get the next cell
            let next_cell = next_row.children[cell_index];
            let input = next_cell.querySelector("input, button");
            if (input !== null) {
                input.focus();
            }
        }
    }

    value() {
        let table = [];
        for (let row of this.rows) {
            const row_value = row.value();
            if (row_value !== undefined) {
                table.push(row_value);
            }
        }
        return table;
    }
}
