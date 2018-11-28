# -*- coding: utf-8 -*-
# Copyright (c) 2018, //SEIBERT/MEDIA GmbH and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import attach_print
import json
from six import string_types
from frappe.utils import (get_url, get_formatted_email, cint,
                          validate_email_add, split_emails, time_diff_in_seconds, parse_addr)
from frappe.utils.file_manager import get_file


class Pixelletter(Document):
    pass

@frappe.whitelist()
def make(doctype=None, name=None, send_email=False, print_html=None, print_format=None, attachments='[]', print_letterhead=True, attach_field=None):

    pdfs = []

    comm = frappe.get_doc({
        "doctype":"Pixelletter",
        "reference_doctype": doctype,
        "reference_name": name,
        "has_attachment": 1 if attachments else 0
    })
    comm.insert(ignore_permissions=True)

    if not doctype:
        # if no reference given, then send it against the communication
        comm.db_set(dict(reference_doctype='Pixelletter', reference_name=comm.name))

    if isinstance(attachments, string_types):
        attachments = json.loads(attachments)

    if print_html or print_format:
        pdfs.append({"print_format_attachment":1, "doctype":comm.reference_doctype, "name":comm.reference_name, "print_format":print_format, "html":print_html})

    if attachments:
        add_attachments(comm.name, attachments)

    if pdfs:
        for a in pdfs:
            if a.get("print_format_attachment") == 1:
                print_format_file = frappe.attach_print(doctype = a.get("doctype"), name = a.get("name"), print_format=a.get("print_format"))
                _file = frappe.get_doc({
                    "doctype": "File",
                    "file_name": print_format_file.get("fname"),
                    "attached_to_doctype": comm.doctype,
                    "attached_to_name": comm.name,
                    "attached_to_field": attach_field,
                    "folder": "Home/Attachments",
                    "is_private": True,
                    "content": print_format_file.get("fcontent"),
                    "decode": False})
                _file.save()


    frappe.db.commit()

    return {
        "name": comm.name,
    }

def add_attachments(name, attachments):
    '''Add attachments to the given Communiction'''
    from frappe.utils.file_manager import save_url

    # loop through attachments
    for a in attachments:
        if isinstance(a, string_types):
            attach = frappe.db.get_value("File", {"name":a},
                                         ["file_name", "file_url", "is_private"], as_dict=1)

            # save attachments to new doc
            save_url(attach.file_url, attach.file_name, "Pixelletter", name,
                     "Home/Attachments", attach.is_private)