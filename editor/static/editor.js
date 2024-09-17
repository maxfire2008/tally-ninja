'use strict';
import { Table } from './editor/Table.js';

class Editor {
    constructor(data, doc_type) {
        this.init(data, doc_type);
    }

    init(data, doc_type) {
        this.data = data;
        this.doc_type = doc_type;

        this.table = new Table(this.data);

        document.getElementById('editor').appendChild(this.table.html());
    }
}
