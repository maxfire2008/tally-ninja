'use strict';

export class NumberInputCell {
    constructor(value, config) {
        this.init(value, config);
    }

    init(value, config) {
        this.value = value;
        this.config = config;
    }

    html(index) {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('td');
        this.element.classList.add('number_input_cell');

        this.input = document.createElement('input');
        this.input.dataset.index = index;
        this.input.type = 'number';
        this.input.min = 1;
        this.input.value = this.value;

        this.input.addEventListener('input', () => {
            this.value = this.input.value;
        });

        this.element.appendChild(this.input);

        return this.element;
    }

    focus() {
        this.input.focus();
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