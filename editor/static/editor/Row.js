'use strict';
export class Row {
    constructor(data) {
        this.init(data);
    }

    init(data) {
        this.cells = [];

        this.data = data;

        this.element = document.createElement('tr');
    }

    appendCell(type, key, config) {
        if (key === "!delete") {
            let cell = new type(null, config, this.delete.bind(this));
            this.cells.push(
                {
                    "cell": cell,
                    "key": key,
                }
            );
            this.element.appendChild(cell.html());
        } else {
            const key_split = key.split('.');
            let value;
            if (key in this.data) {
                value = this.data[key];
            } else {
                value = this.data;
                while (key_split.length > 0) {
                    value = value[key_split.shift()];
                }
            }


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
            if (cell.cell.value !== undefined && cell.key !== "!delete") {
                row[cell.key] = cell.cell.value;
            }
        }
        return row;
    }
}
