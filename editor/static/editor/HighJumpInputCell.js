'use strict';

export class HighJumpInputCell {
    constructor(value, config) {
        this.init(value, config);
    }

    init(value, config) {
        this.value = value;
        this.config = config;
    }

    html() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('td');

        this.input = document.createElement('input');
        this.input.type = 'text';

        this.input.addEventListener('input', () => {
            this.value = this.input.value;
        });

        this.element.appendChild(this.input);

        return this.element;
    }

    destroyHtml() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }
    }

    value() {
        return this.value;
    }
}