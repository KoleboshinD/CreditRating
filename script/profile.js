function requestCredit(bankId, bankName) {
    let amount = prompt(`Введите сумму кредита в ${bankName}:`, "100000");
    if (amount && !isNaN(amount) && amount > 0) {
        fetch('/credit_request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bank_id: bankId,
                amount: parseFloat(amount)
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.status === 'approved') {
                        alert(`Заявка одобрена!\nСумма: ${data.approved_amount} ₽`);
                    } else {
                        alert(`Заявка отклонена\n${data.message}`);
                    }
                    location.reload();
                } else {
                    alert(`Ошибка: ${data.message}`);
                }
            })
            .catch(error => {
                alert('Ошибка при отправке заявки');
            });
    } else if (amount) {
        alert('Пожалуйста, введите корректную сумму');
    }
}