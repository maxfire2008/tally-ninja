'use strict';
export class Row {
    constructor() {
        this.init();
    }

    init() {
        this.cells = [];
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
            return cell;
        } else {
            let cell = new type(value, config);
            this.cells.push(
                {
                    "cell": cell,
                    "key": key,
                }
            );
            return cell;
        }
    }

    html() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('tr');
        this.element.dataset.index = this.index;

        for (let [index, cell] of this.cells.entries()) {
            this.element.appendChild(cell.cell.html(index));
        }

        return this.element;
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
