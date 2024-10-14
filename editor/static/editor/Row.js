'use strict';
export class Row {
    constructor() {
        this.init();
    }

    init() {
        this.cells = [];

        this.element = document.createElement('tr');
    }

    appendCell(type, value, key, config) {
        if (key === "!delete") {
            let cell = new type(value, config, this.delete.bind(this));
            this.cells.push(
                {
                    "cell": cell,
                    "key": key,
                }
            );
            this.element.appendChild(cell.html());
        } else {
            let cell = new type(value, config);
            this.cells.push(
                {
                    "cell": cell,
                    "key": key,
                }
            );
            this.element.appendChild(cell.html());
        }
    }

    delete() {
        this.element.remove();
        this.value = function () { return undefined; }
    }

    focus(i) {
        this.cells[i].cell.focus();
    }

    value() {
        let row = {};
        for (let cell of this.cells) {
            if (cell.cell.value !== undefined) {
                row[cell.key] = cell.cell.value;
            }
        }
        return row;
    }
}
