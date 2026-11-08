from celery import shared_task
@shared_task
def remind_birthdays():
    return 'Tug‘ilgan kun eslatmalari tekshirildi'
