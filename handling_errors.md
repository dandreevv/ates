### 1. Transactional Outbox

Данный паттерн поможет не терять сообщения при
- сетевых ошибках
- падении брокера

Продьюсер, который будет перетаскивать сообщения из таблицы в брокер будет иметь retry стратегию и обрабатывать события последовательно.


### 2. DLQ через БД
Если консьюмер не может обработать сообщение мы будем складывать его в БД