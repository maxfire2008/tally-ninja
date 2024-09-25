'use strict';

export class DeleteButtonCell {
    constructor(value, config, callback) {
        this.init(value, config, callback);
    }

    init(value, config, callback) {
        this.value = value;
        this.config = config;
        this.callback = callback;
    }

    html() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('td');

        this.button = document.createElement('button');
        this.button.textContent = "Delete";
        this.button.addEventListener('click', this.callback);

        this.element.appendChild(this.button);

        return this.element;
    }

    destroyHtml() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }
    }

    focus() {
        this.input.focus();
    }

    value() {
        return this.value;
    }
}