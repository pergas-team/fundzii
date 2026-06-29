import requests
import json

# from apps.order.models import PaymentRecord


class SharifPayment():
    def __init__(self):
        self.url = 'https://pay.sharif.edu/api/API'
        self.init_data = {
            "TerminalID": 30000,
            "Username": "clabUser",
            "Password": "pAMxeZpANQ",
        }
        print('s')
        self.PAYURL = 'pay.sharif.edu'

    def pay_request(self, user, payment_record):
        data = self.init_data
        data.update({"FN": "Request",
                 "Amount": int(payment_record.amount),
                 "CallbackURL": "https://lims.labs.sharif.ir/dashboard/customer/payment/confirm?",
                 # "CallbackURL": "https:\/\/lims.radif.app/dashboard/customer/payment/confirm?",
                 "ID2": str(payment_record.transaction_code),
                 "IsForeigner": 0,
                 "NC": user.national_id,
                 "Name": user.first_name[:28],
                 "Family": user.last_name[:28],
                 "Tel": user.username.replace("+98", "0"),
                 "Mobile": user.username.replace("+98", "0"),
                 "EMail": user.email
                 })
        response = requests.post(self.url, data={"INPUT": json.dumps(data)})
        r = json.loads(response.text)
        payment_record.payment_order_id = r["OrderID"]
        if r['Result'] != 0:
            payment_record.log_text = payment_record.log_text + str(r)
            payment_record.save()
            return False, response
        payment_record.payment_order_guid = r["OrderGUID"]
        payment_record.payment_order_id = r["OrderID"]
        payment_record.payment_link = f'https://{self.PAYURL}/submit2/{r["OrderID"]}/{r["OrderGUID"]}'
        payment_record.save()

        return True, response

    def status_check(self, payment_record):
        data = self.init_data
        data.update({
            'FN': 'Status2',
            'OrderID': payment_record.payment_order_id,
            'OrderGUID': payment_record.payment_order_guid,
        })
        response = requests.post(self.url, data={"INPUT": json.dumps(data)})
        return json.loads(response.text)

    def pay_confirm(self, payment_record, Result):
        if Result == 0:
            data = self.init_data
            data.update({'FN': 'Status2',
                         "OrderID": payment_record.payment_order_id,
                         "OrderGUID": payment_record.payment_order_guid
                         })

            response = requests.post(self.url, data={"INPUT": json.dumps(data)})
            r = json.loads(response.text)
            if r['Result'] == 0:
                payment_record.called_back = True
                payment_record.tref = r['ReferenceID']
                payment_record.set_payed()
                payment_record.save()
                return True
            else:
                return False
        else:
            return False





# response_ex = {
#         "Result": 0,
#         "Message": "درخواست پرداخت با موفقیت ثبت شد",
#         "Focus": "",
#         "OrderID": 140541566,
#         "OrderGUID": "B479CC76-1EB1-4092-BE5A-706B0CAFD5BC"
#     }
# if r['Result'] == -1:
#     r = response_ex
# OrderID = r["OrderID"]
# OrderGUID = r["OrderGUID"]

# return f'https://{self.PAYURL}/submit2/{r["OrderID"]}/{r["OrderGUID"]}'









