'use strict';
import { Table } from './editor/Table.js';
import { HighJumpInputCell } from './editor/HighJumpInputCell.js';

export class Editor {
    constructor(data, doc_type, event_info, config) {
        this.init(data, doc_type, event_info, config);
    }

    init(data, doc_type, event_info, config) {
        this.data = data;
        this.doc_type = doc_type;
        this.event_info = event_info;
        this.config = config;

        this.table = new Table(this.data[this.doc_type], this.event_info.event_type, doc_type, this.config);

        const editorHolder = document.getElementById('editorHolder')
        editorHolder.appendChild(this.table.element);

        if (this.event_info.event_type === 'race') {
            const newLaneButton = document.createElement('button');
            newLaneButton.innerHTML = 'New Lane';
            newLaneButton.addEventListener('click', this.newLane.bind(this));
            editorHolder.appendChild(newLaneButton);

            const newHeatButton = document.createElement('button');
            newHeatButton.innerHTML = 'New Heat';
            newHeatButton.addEventListener('click', this.newHeat.bind(this));
            editorHolder.appendChild(newHeatButton);
        } else if (this.event_info.event_type === 'high_jump') {
            const newHeightButton = document.createElement('button');
            newHeightButton.innerHTML = 'New Height';
            newHeightButton.addEventListener('click', this.newHeight.bind(this));
            editorHolder.appendChild(newHeightButton);
        }

        this.saveButton = document.createElement('button');
        this.saveButton.innerHTML = 'Save';
        this.saveButton.addEventListener('click', () => {
            this.save();
        });
        editorHolder.appendChild(this.saveButton);

        this.keydown = this.keydown.bind(this);
        document.addEventListener('keydown', this.keydown);
    }

    currentLane() {
        const lanes = this.table.value().map(row => row.lane);
        lanes.push(0);
        return Math.max(...lanes);
    }

    currentHeat() {
        const heats = this.table.value().map(row => row.heat);
        heats.push(1);
        return Math.max(...heats);
    }

    newLane() {
        this.table.appendRow({
            lane: this.currentLane() + 1,
            heat: this.currentHeat(),
        });
    }

    newHeat() {
        this.table.appendRow({
            lane: 1,
            heat: this.currentHeat() + 1,
        });
    }

    newHeight() {
        let height = prompt("Enter the new height");
        this.table.appendColumn(
            {
                "type": HighJumpInputCell,
                "key": height,
                "heading": height,
            }
        )
    }

    keydown(event) {
        if (this.event_info.event_type === 'race') {
            // Shift + L is for new lane
            if (event.shiftKey && event.key === 'L') {
                this.newLane();
            }
            // Shift + H is for new heat
            if (event.shiftKey && event.key === 'H') {
                this.newHeat();
            }
        } else if (this.event_info.event_type === 'high_jump') {
            // Shift + H is for new height
            if (event.shiftKey && event.key === 'H') {
                this.newHeight();
            }
        }
    }

    save() {
        const data = this.table.value();
        console.log('data', data);
        // this.data[this.doc_type] = data;
        // fetch('/api/save', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        //     body: JSON.stringify(this.data),
        // }).then(response => {
        //     if (response.ok) {
        //         alert('Data saved');
        //     } else {
        //         alert('Error saving data');
        //     }
        // });
    }
}
