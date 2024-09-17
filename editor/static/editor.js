'use strict';
import { Table } from './editor/Table.js';

export class Editor {
    constructor(data, doc_type, event_info) {
        this.init(data, doc_type, event_info);
    }

    init(data, doc_type, event_info) {
        this.data = data;
        this.doc_type = doc_type;
        this.event_info = event_info;

        this.table = new Table(this.data[this.doc_type], this.event_info.event_type);

        document.getElementById('editorHolder').appendChild(this.table.html());
    }
}
