import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class Add extends StatefulWidget {
  const Add({super.key});

  @override
  State<Add> createState() => _AddState();
}

class _AddState extends State<Add> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _itemController = TextEditingController();
  final TextEditingController _quantityController = TextEditingController();
  final TextEditingController _batchNoController = TextEditingController();
  final TextEditingController _priceController = TextEditingController();

  late FocusNode _itemfocus;
  late FocusNode _quantityfocus;
  late FocusNode _batchnofocus;
  late FocusNode _pricefocus;

  DateTime? _manufactureDate;
  DateTime? _expiryDate;
  String? _selectedDealer;
  List<String> _dealerNames = [];

  String? _resultMessage;

  // ignore: unused_field
  IconData? _resultIcon;

  final mainUrl = "https://api.svp.com.np";

  @override
  void initState() {
    super.initState();
    _fetchDealerNames();
    _itemfocus = FocusNode();
    _quantityfocus = FocusNode();
    _batchnofocus = FocusNode();
    _pricefocus = FocusNode();
  }

  @override
  void dispose() {
    _itemController.dispose();
    _quantityController.dispose();
    _batchNoController.dispose();
    _priceController.dispose();

    _itemfocus.dispose();
    _pricefocus.dispose();
    _quantityfocus.dispose();
    _batchnofocus.dispose();

    super.dispose();
  }

  Future<void> _fetchDealerNames() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String key = prefs.getString('key') ?? '';

    final url = Uri.parse('$mainUrl/dealers?key=$key');
    try {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        setState(() {
          if (data.isNotEmpty && data.first is String) {
            _dealerNames = List<String>.from(data);
          } else {
            throw Exception('Invalid response format');
          }
        });
      } else {
        throw Exception('Failed to fetch dealers: ${response.statusCode}');
      }
    } catch (e) {
      _showErrorDialog('Failed to fetch dealer names');
    }
  }

  void _showErrorDialog(String message) {
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text(
            'Error',
            style: TextStyle(color: Colors.black),
          ),
          content: Text(
            message,
            style: const TextStyle(color: Colors.black),
          ),
          actions: <Widget>[
            TextButton(
              child: const Text(
                'OK',
                style: TextStyle(color: Colors.black),
              ),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
          backgroundColor: Colors.red[100],
        );
      },
    );
  }

  Future<void> _selectDate(BuildContext context, bool isManufactureDate) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime(2101),
    );
    if (picked != null && picked != DateTime.now()) {
      setState(() {
        if (isManufactureDate) {
          _manufactureDate = picked;
        } else {
          _expiryDate = picked;
        }
      });
    }
  }

  void _submitForm() {
    if (_formKey.currentState!.validate() &&
        _manufactureDate != null &&
        _expiryDate != null &&
        _selectedDealer != null) {
      _addItem();
    } else {
      _showErrorDialog('Please fill in all fields');
    }
  }

  Future<void> _addItem() async {
    final String item = _itemController.text;
    final int quantity = int.parse(_quantityController.text);
    final String batchNo = _batchNoController.text;
    final String manufactureDate = _manufactureDate!.toIso8601String();
    final String expiryDate = _expiryDate!.toIso8601String();
    final double price = double.parse(_priceController.text);
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String key = prefs.getString('key') ?? '';
    final url = Uri.parse('$mainUrl/add-item');
    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'item': item,
          'quantity': quantity,
          'batchNo': batchNo,
          'manufactureDate': manufactureDate,
          'expiryDate': expiryDate,
          'price': price,
          'dealerName': _selectedDealer,
          'key': key,
        }),
      );

      if (response.statusCode == 200) {
        setState(() {
          _resultMessage = 'Item added successfully';
          _resultIcon = Icons.check;
        });
        _itemController.clear();
        _quantityController.clear();
        _batchNoController.clear();
        _priceController.clear();
        setState(() {
          _manufactureDate = null;
          _expiryDate = null;
          _selectedDealer = null;
        });
        _showSuccessDialog(_resultMessage!);
      } else {
        throw Exception('Failed to add item: ${response.body}');
      }
    } catch (e) {
      setState(() {
        _resultMessage = 'Failed to add item: $e';
        _resultIcon = Icons.error;
      });
      _showErrorDialog(_resultMessage!);
    }
  }

  void _showSuccessDialog(String message) {
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text(
            'Success',
            style: TextStyle(color: Colors.black),
          ),
          content: Text(
            message,
            style: TextStyle(color: Colors.black),
          ),
          actions: <Widget>[
            TextButton(
              child: const Text(
                'OK',
                style: TextStyle(color: Colors.black),
              ),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
          backgroundColor: Colors.green[100],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Add Items"),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                TextFormField(
                  controller: _itemController,
                  focusNode: _itemfocus,
                  decoration: const InputDecoration(
                    labelText: 'Item',
                    prefixIcon: Icon(Icons.shopping_bag),
                    border: UnderlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter an item';
                    }
                    return null;
                  },
                  onFieldSubmitted: (value) {
                    FocusScope.of(context).requestFocus(_quantityfocus);
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _quantityController,
                  focusNode: _quantityfocus,
                  decoration: const InputDecoration(
                    labelText: 'Quantity',
                    prefixIcon: Icon(Icons.format_list_numbered),
                    border: UnderlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter the quantity';
                    }
                    if (int.tryParse(value) == null) {
                      return 'Please enter a valid number';
                    }
                    return null;
                  },
                  onFieldSubmitted: (value) {
                    FocusScope.of(context).requestFocus(_batchnofocus);
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _batchNoController,
                  focusNode: _batchnofocus,
                  decoration: const InputDecoration(
                    labelText: 'Batch No',
                    prefixIcon: Icon(Icons.confirmation_number),
                    border: UnderlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter the batch number';
                    }
                    return null;
                  },
                  onFieldSubmitted: (value) {
                    FocusScope.of(context).requestFocus(_pricefocus);
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _priceController,
                  focusNode: _pricefocus,
                  decoration: const InputDecoration(
                    labelText: 'Price',
                    prefixIcon: Icon(Icons.attach_money),
                    border: UnderlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter the price';
                    }
                    if (double.tryParse(value) == null) {
                      return 'Please enter a valid price';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                ListTile(
                  title: Text(
                    _selectedDealer ?? 'Select Dealer',
                    style: TextStyle(
                      color:
                          _selectedDealer == null ? Colors.grey : Colors.green,
                    ),
                  ),
                  onTap: () {
                    _showDealerPicker();
                  },
                  leading: const Icon(Icons.person),
                ),
                const SizedBox(height: 16),
                ListTile(
                  title: Text(
                    _manufactureDate == null
                        ? 'Select Manufacture Date'
                        : 'Manufacture Date: ${_manufactureDate!.toLocal().toString().split(' ')[0]}',
                    style: TextStyle(
                      color:
                          _manufactureDate == null ? Colors.grey : Colors.green,
                    ),
                  ),
                  onTap: () => _selectDate(context, true),
                  leading: const Icon(Icons.calendar_today),
                ),
                const SizedBox(height: 16),
                ListTile(
                  title: Text(
                    _expiryDate == null
                        ? 'Select Expiry Date'
                        : 'Expiry Date: ${_expiryDate!.toLocal().toString().split(' ')[0]}',
                    style: TextStyle(
                      color: _expiryDate == null ? Colors.grey : Colors.green,
                    ),
                  ),
                  onTap: () => _selectDate(context, false),
                  leading: const Icon(Icons.calendar_today),
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: _submitForm,
                  style: ElevatedButton.styleFrom(
                    foregroundColor: Colors.white,
                    backgroundColor: Colors.orange,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text('Add Item'),
                )
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showDealerPicker() {
    showDialog<void>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Select Dealer'),
          content: SizedBox(
            width: double.maxFinite,
            height: 300,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ListView.builder(
                    shrinkWrap: true,
                    itemCount: _dealerNames.length,
                    itemBuilder: (BuildContext context, int index) {
                      final dealer = _dealerNames[index];
                      return Container(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.blue),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: ListTile(
                          title: Text(
                            dealer,
                            style: const TextStyle(color: Colors.blue),
                          ),
                          onTap: () {
                            setState(() {
                              _selectedDealer = dealer;
                            });
                            Navigator.of(context).pop();
                          },
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
          actions: <Widget>[
            TextButton(
              child: const Text('Cancel'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
        );
      },
    );
  }
}
