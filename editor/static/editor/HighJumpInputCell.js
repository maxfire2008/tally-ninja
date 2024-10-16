'use strict';

export class HighJumpInputCell {
    constructor(value, config) {
        this.init(value, config);
    }

    init(value, config) {
        this.config = config;
        this.attempts = [];
        let previous = null;
        for (let i = 0; i < 3; i++) {
            if (this.attempts.length === 0) {
                this.attempts.push(new Attempt(this.value[i], null));
            } else {
                this.attempts.push(new Attempt(this.value[i], this.attempts[this.attempts.length - 1]));
            }
            if (previous !== null) {
                previous.next = this.attempts[this.attempts.length - 1];
            }
            previous = this.attempts[this.attempts.length - 1];
        }
    }

    html() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('td');

        this.div = document.createElement('div');
        this.div.classList.add('high_jump_input_cell');

        this.element.appendChild(this.div);

        for (let attempt of this.attempts) {
            this.div.appendChild(attempt.html());
        }

        return this.element;
    }

    destroyHtml() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }
    }

    value() {
        const val = [];
        for (let attempt of this.attempts) {
            const av = attempt.value()
            if (av !== undefined) {
                val.push(av);
            }
        }
        return val;
    }
}

class Attempt {
    constructor(value, previous) {
        this.init(value, previous);
    }

    init(value, previous) {
        this.value = value;
        this.previous = previous;
        this.next = null;
    }

    html() {
        if (this.element !== undefined) {
            this.element.remove();
            delete this.element;
        }

        this.element = document.createElement('button');

        this.updateHtml();

        this.element.addEventListener('click', this.click.bind(this));

        return this.element;
    }

    updateHtml() {
        if (this.value === true) {
            this.element.textContent = '✔';
        } else if (this.value === false) {
            this.element.textContent = '✘';
        } else {
            this.element.textContent = '-';
        }
    }

    click(event) {
        // if the user is holding shift, then we use alternative logic
        if (event.shiftKey) {
            // just do what the user says without any checks
            if (this.value === false) {
                this.value = true;
            } else if (this.value === true) {
                this.value = undefined;
            } else {
                this.value = false;
            }
        } else {
            if (this.next !== null && this.next.value !== undefined) {
                return;
            }
            if ((this.previous === null || this.previous.value === false) && this.value === undefined) {
                this.value = false;
            } else if ((this.next === null || this.next.value === undefined) && this.value === false) {
                this.value = true;
            } else {
                this.value = undefined;
            }
        }

        this.updateHtml();
    }

    value() {
        return this.value;
    }
}