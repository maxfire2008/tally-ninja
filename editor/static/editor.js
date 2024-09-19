'use strict';
import { Table } from './editor/Table.js';

export class Editor {
    constructor(data, doc_type, event_info, config) {
        this.init(data, doc_type, event_info, config);
    }

    init(data, doc_type, event_info, config) {
        this.data = data;
        this.doc_type = doc_type;
        this.event_info = event_info;
        this.config = config;

        this.table = new Table(this.data[this.doc_type], this.event_info.event_type, config);

        document.getElementById('editorHolder').appendChild(this.table.html());
    }
}
