'use strict';
export class Row {
    constructor() {
        this.init();
    }

    init() {
        this.cells = [];
    }

    appendCell(type, value) {
        let cell = new type(value);
        this.cells.push(cell);
        return cell;
    }
}
