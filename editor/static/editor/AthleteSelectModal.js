function populateModal(modalContent, callback) {
    let input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Search...';
    input.addEventListener('input', () => {
        let search = input.value;
        let results = searchAthletes(search);
        this.populateResults(results, callback);
    });
    modalContent.appendChild(input);
}

export function athleteSelectModal(callback) {
    let modal = document.createElement('div');
    modal.className = 'modal';

    let modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    populateModal(modalContent, callback);
    modal.appendChild(modalContent);

    let span = document.createElement('span');
    span.className = 'close';
    span.textContent = '&times;';
    span.addEventListener('click', () => {
        modal.remove();
    });

    document.body.appendChild(modal);
}