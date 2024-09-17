'use strict';
export class AthleteInputCell {
    constructor(value) {
        this.init(value);
    }

    init(value) {
        this.value = value;
    }

    html() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('input');
        this.element.type = 'text';
        this.element.value = this.value;
        this.element.addEventListener('input', () => {
            this.value = this.element.value;
        });
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