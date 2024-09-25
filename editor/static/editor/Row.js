'use strict';
export class Row {
    constructor() {
        this.init();
    }

    init(index) {
        this.cells = [];
    }

    appendCell(type, value, key, config) {
        let cell = new type(value, config);
        this.cells.push(
            {
                "cell": cell,
                "key": key,
            }
        );
        return cell;
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

    focus(i) {
        this.cells[i].cell.focus();
    }

    value() {
        let row = {};
        for (let cell of this.cells) {
            row[cell.key] = cell.cell.value;
        }
        return row;
    }
}
