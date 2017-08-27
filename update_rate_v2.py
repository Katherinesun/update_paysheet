############################################################
# To be configured by the user
paysheet_in = "PAYTSHT.INP"
paysheet_out = "PAYTSHT.INP.NEW"
rows_updated = "PAYTSHT.INT.ROWS.UPDATED"
partime_rates_defined = [20.20, 21.24]
casual_rates_defined = [23.82, 25.25, 25.42, 25.77, 26.56]
sat_multiplier = 1.4
sun_multiplier = 1.6
internet_old_rate = 1.500
internet_new_rate = 1.250
# set leave_loading_percentage to a number (percentage) without % sign
leave_loading_percentage = 17.5
############################################################

# Change the rate to 3 decimals and in string type
casual_rates = set(["%.3f" % x for x in casual_rates_defined])
internet_old_rate_s = "%.3f" % internet_old_rate
internet_new_rate_s = "%.3f" % internet_new_rate


def update_weekend_casual_rate(columns):
    columns[4] = 'N'
    columns[5] = paytype + 'CAS'
    if paytype == 'SAT':
        columns[9] = "%.3f" % (float(columns[9]) * sat_multiplier)
    elif paytype == 'SUN':
        columns[9] = "%.3f" % (float(columns[9]) * sun_multiplier)
    return columns

def add_internet_allowance(last_ORD_row, cumulative_hours):
    new_row = list(last_ORD_row)
    new_row[4] = 'A'
    new_row[5] = 'INTERNET'
    if cumulative_hours > 20:
        new_row[6] = '2.000'
    else:
        new_row[6] = '1.000'
    new_row[9] = internet_new_rate_s
    return new_row


if __name__ == "__main__":
    with open(paysheet_in, 'rb') as in_file, \
         open(paysheet_out, 'wb') as out_file, \
         open(rows_updated, 'wb') as delta_file:
        write_to_delta_file = lambda line, col_list: delta_file.write(
                              'line %s: ' % line + ','.join(col_list))
        write_to_out_file = lambda col_list: out_file.write(','.join(col_list))

        i = 0  # line counter for the out_file
        incount = 0 # line counter for the in_file
        last_weekday_rate = 0.0
        employee_id = None
        prev_employee_id = None
        # For cum_ord_hours, key is employee_id, value is the cumulative value
        # of col7 for that employee_id when col6 = ORD
        cumulative_hours = {}
        last_ORD_row = []

        for row in in_file:
            i += 1
            incount += 1
            columns = row.split(',')
            prev_employee_id = employee_id
            employee_id = columns[2]
            A_or_N = columns[4]
            paytype = columns[5]
            hours = float(columns[6])
            rate = columns[9]

            # Add INTERNET allowance to every staff
            # Assuming all the data related to an employee are put together in
            # consecutive rows
            if ((prev_employee_id is not None) and
                (employee_id != prev_employee_id) and
                (prev_employee_id in cumulative_hours)):
                new_row = add_internet_allowance(last_ORD_row,
                          cumulative_hours[prev_employee_id])
                # Write out the new row for internet allowance
                write_to_delta_file(i, new_row)
                write_to_out_file(new_row)
                i += 1

            if paytype == 'ORD':
                if A_or_N == 'N':
                    # This row is for weekday ordinary rate
                    # Update the last weekday rate if col5 == N and col6 == ORD
                    last_weekday_rate = rate
                write_to_out_file(columns)

                # Update the cumulative_hours
                if employee_id not in cumulative_hours:
                    cumulative_hours[employee_id] = hours
                else:
                    cumulative_hours[employee_id] += hours

                # Store the last ORD row
                last_ORD_row = list(columns)

            # Update the rate for casual workers on SAT and SUN
            elif paytype == 'SAT' or paytype == 'SUN':
                if (A_or_N == 'A') and (last_weekday_rate in casual_rates):
                    # it's weekend and it's for casual workers, update the rate
                    update_weekend_casual_rate(columns)
                    write_to_delta_file(i, columns)
                write_to_out_file(columns)

            # Update the rate for INTERNET
            elif paytype == 'INTERNET':
                if rate == internet_old_rate_s:
                    # Update internet rate
                    columns[9] = internet_new_rate_s
                    write_to_delta_file(i, columns)
                write_to_out_file(columns)

            # Update SL to PCL for col6
            elif paytype == 'SL':
                # Update col6 from SL to PCL
                columns[5] = 'PCL'
                write_to_delta_file(i, columns)
                write_to_out_file(columns)

            # Add a new row for 'leave loading when col6 = AL
            elif paytype == 'AL':
                new_row = list(columns)
                new_row[5] = 'LL'  # set the paytype to LL
                new_row[9] = "%.3f" % (
                             float(rate) * leave_loading_percentage / 100)
                write_to_out_file(columns)
                write_to_delta_file(i, new_row)
                write_to_out_file(new_row)
                i += 1

            # Write the columns out by default if no logics apply
            else:
                write_to_out_file(columns)

        else:
            # Finish reading the in_file
            # Add the internet allowance for the last employee
            new_row = add_internet_allowance(last_ORD_row,
                      cumulative_hours[employee_id])
            # Write out the new row for internet allowance
            i += 1
            write_to_delta_file(i, new_row)
            write_to_out_file(new_row)
