import ib_insync as ibi
import xlwings as xw
import asyncio

def accountValue(accountNumber, tag: str) -> str:
    """Return account value for the given tag."""
    return next((
        v.value for v in ib.accountValues(accountNumber)
        if v.tag == tag and v.currency == 'BASE'), '')


def updateAccountAndPortfolio(accountNumber):

    #get name of Excel worksheet for the account number received, so updates can be made to the correct worksheet
    sheetName = accountNumberToSheet.get(accountNumber)

    #Set NVL and Cash values in Excel cells
    wb.sheets(sheetName).range("B1").value = accountValue(accountNumber, 'NetLiquidationByCurrency')
    wb.sheets(sheetName).range("D1").value = accountValue(accountNumber, 'CashBalance')

    acccountPositions = []
    for acccountPosition in ib.positions():
        #ib.reqPnLSingle(account=portfolioItem.account, conId=portfolioItem.contract.conId, modelCode='')
        acccountPositions.append([acccountPosition.contract.localSymbol, acccountPosition.position, float(acccountPosition.avgCost)*float(acccountPosition.position), acccountPosition.unrealizedPNL])
    acccountPositions.sort()
    #wb.sheets(sheetName).range(range("A5"), range("A5").offset(0, 3).end('down')).clear_contents()
    wb.sheets(sheetName).range("A5").options(ndim=2).value = acccountPositions


def closePositions(xlSheetName):
    raise ValueError ("Yet to write this function")


def getIbConnectionPort(xlSheetName):
    # return the socket port number to use for connecting to TWS
    if xlSheetName == "Paper":
        return 7497
    else:
        return 7496


def readAndPlaceXLOrders():
    sheetToAccountNumber = {"Brokerage": "Add account number here"}
    accountNumberToSheet = {"Add account number here": "Brokerage"}

    wb = xw.Book.caller()
    ib = ibi.IB()
    ordersCallingWorksheet = wb.sheets.active.name

    # Start a new IB connection
    ib.connect('127.0.0.1', getIbConnectionPort(ordersCallingWorksheet), clientId=2)

    ordersFromXL = []

    if wb.sheets(ordersCallingWorksheet).range("A20").value.strip() == "":
        raise ValueError ("No Orders to Submit")
    else:
        ordersFromXL = wb.sheets(ordersCallingWorksheet).range("A20").options(expand='table').value

    # Place orders one at a time
    for order in ordersFromXL:
        if order[2].upper() == "LMT":
            entryOrder = ibi.LimitOrder(order[1], int(order[5]), order[4])
        elif order[2].upper() == "MKT":
            entryOrder = ibi.MarketOrder(order[1], int(order[5]))
        else:
            raise ValueError ("Incorrect Order Type in " + order[0])

        if order[7].upper() == "STK":
            contract = ibi.Stock(order[7], 'SMART', 'USD', primaryExchange='NYSE')
        elif order[7].upper() == "OPT":
            contract = ibi.Option(order[7], "20" + order[8].strftime("%y%m%d"), order[9], order[10], 'SMART', multiplier=100, currency='USD')
            ib.qualifyContracts(contract)
        else:
            raise ValueError ("Incorrect instrument type")
        ib.placeOrder(contract, entryOrder)

    # Disconnect from IB after placing the orders
    ib.disconnect()


def globalCancelOrders():
    ib.reqGlobalCancel()


def main():
    global ib, wb, portfolioItems, sheetToAccountNumber, accountNumberToSheet
    sheetToAccountNumber = {"Brokerage":"Add account number here"}
    accountNumberToSheet = {"Add account number here":"Brokerage"}

    #controller = ibi.IBController('TWS', '969', 'paper',
    #    TWSUSERID='enter username here', TWSPASSWORD='enter password here')
    ib = ibi.IB()
    #ib.sleep(30)

    #Create an object for the caller Excel workbook and note the calling worksheet
    wb = xw.Book.caller()

    # Start IB api connection
    ib.connect('127.0.0.1', getIbConnectionPort(wb.sheets.active.name), clientId=1)

    loop = asyncio.get_event_loop()

    for accountNumber in accountNumberToSheet:
        updateAccountAndPortfolio(accountNumber)

    ib.sleep(120)

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    ib.disconnect()
    ib.sleep(0.1)

if __name__ == "__main__":
    xw.Book("ib_insync_XL.xlsm").set_mock_caller()
    main()